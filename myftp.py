import socket
from getpass import getpass
import time

client_socket = None
host = None

def send_cmd(socket, cmd):
    socket.sendall(f"{cmd}\r\n".encode())

def get_resp(socket):
    return socket.recv(1024).decode()

def ascii():
    try:
        send_cmd(client_socket, "TYPE A")
        print(get_resp(client_socket), end="")
    except:
        print("Not connected.")

def binary():
    try:
        send_cmd(client_socket, "TYPE I")
        print(get_resp(client_socket), end="")
    except:
        print("Not connected.")

def cd(dir):
        if not host:
            print("Not connected.")
            return
        if not dir:
            dir = input("Remote directory ")
        send_cmd(client_socket, f"CWD {dir}")
        print(get_resp(client_socket), end="")

def rename(filename , new_filename = None):
        if not host:
            print("Not connected.")
            return
        if not filename:
            filename = input("From name ")
        if not new_filename:
            new_filename = input("To name ")
        send_cmd(client_socket, f"RNFR {filename}")
        resp = get_resp(client_socket)
        print(resp, end="")
        if resp.split()[0] == '550':
            return
        send_cmd(client_socket, f"RNTO {new_filename}")
        print(get_resp(client_socket), end="")


def delete(filename):
        if not host:
            print("Not connected.")
            return
        if not filename:
            filename = input("Remote file ")
        send_cmd(client_socket, f"DELE {filename}")
        print(get_resp(client_socket), end="")

def open_data_conn():
    global host

    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.bind((host, 0))
    data_sock.listen()
    port = data_sock.getsockname()[1]

    host_part = host.replace('.', ',')
    port = f"{port:016b}"
    port_1 = int(port[0:8], 2)
    port_2 = int(port[8:16], 2)
    send_cmd(client_socket,f"PORT {host_part},{port_1},{port_2}")
    print(get_resp(client_socket), end="")
    return data_sock

def recv_data(data_sock):
    data_conn, data_addr = data_sock.accept()
    # print(data_conn)
    size = 0
    data = ""
    while True:
        data_part = data_conn.recv(1024)
        if data_part:
            data += data_part.decode()
            # print(data)
            size += len(data_part)
        else:
            break
    return data, size

def send_data(data_sock, file):
    data_conn, _ = data_sock.accept()
    data = file.read()
    data_conn.sendall(data.encode())
    return len(data)

def ls(dir):
    try:
        data_sock = open_data_conn()

        if dir == None:
            dir = ""
        send_cmd(client_socket, f"NLST {dir}")
        resp = get_resp(client_socket)
        print(resp, end="")

        resp_code = resp.split()[0]
        if resp_code == "550":
            return
        
        start_time = time.time()
        data, size = recv_data(data_sock)
        data_sock.close()
        end_time = time.time()
        elapsed_time = end_time - start_time
        size += 3
        if elapsed_time == 0:
            elapsed_time = 0.0001
        speed = size / (elapsed_time * 1000)
        status = f"ftp: {size} bytes received in {elapsed_time:.2f}Seconds {speed:.2f}Kbytes/sec."

        print(data, end="")
        print(get_resp(client_socket), end="")
        if size != 3:
            print(status)
    except:
        print("Not connected.")

def get(remote_file, local_file = None):
        if not host:
            print("Not connected.")
            return
        if not remote_file:
            remote_file = input("Remote file ")
            local_file = input("Local file ")

        if not local_file or local_file == "":
            local_file = remote_file

        data_sock = open_data_conn()
        send_cmd(client_socket, f"RETR {remote_file}")
        resp = get_resp(client_socket)

        if resp.split()[0] == '550':
            print(resp[:-2], end="")
            return
        
        print(resp, end="")

        start_time = time.time()
        data, size = recv_data(data_sock)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        speed = size / (elapsed_time * 1000)
        status = f"ftp: {size} bytes received in {elapsed_time:.2f}Seconds {speed:.2f}Kbytes/sec."

        f = open(local_file, "w")
        f.write(data)
        f.close()
        data_sock.close()
        print(get_resp(client_socket), end="")
        if size != 0:
            print(status)

def put(local_file, remote_file = None):
        if not host:
            print("Not connected.")
            return
        if not local_file:
            local_file = input("Remote file ")
            remote_file = input("Local file ")

        if not remote_file or remote_file == "":
            remote_file = local_file

        try:
            f = open(local_file, "r")
        except FileNotFoundError:
            print(f"{local_file}: File not found")
            return
        except IOError:
            print(f"Error opening local file {local_file}")
            return

        data_sock = open_data_conn()
        send_cmd(client_socket, f"STOR {local_file}")
        print(get_resp(client_socket), end="")

        start_time = time.time()
        size = send_data(data_sock, f)
        end_time = time.time()

        f.close()
        data_sock.close()
        elapsed_time = end_time - start_time
        if elapsed_time == 0:
            elapsed_time = 0.0001
        speed = size / (elapsed_time * 1000)
        status = f"ftp: {size} bytes received in {elapsed_time:.2f}Seconds {speed:.2f}Kbytes/sec."

        print(get_resp(client_socket), end="")
        if size != 0:
            print(status)

def ftp_open(ip = None, port = 21):
    global client_socket
    global host
    if client_socket:
        print(f"Already connected to {host}, use disconnect first.")
        return
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if not ip:
        ip = input("To ")

    host = ip

    try:
        client_socket.connect((ip, port))
    except ConnectionRefusedError:
        print("> ftp: connect :Connection refused")
        close_sock()
        return
    except socket.timeout:
        print("> ftp: connect :Connection timed out")
        close_sock()
        return
    except socket.gaierror:
        print(f"Unknown host {ip}.")
        close_sock()
        return
    
    print(f"Connected to {ip}.")
    print(get_resp(client_socket), end="")

    send_cmd(client_socket, "OPTS UTF8 ON")
    print(get_resp(client_socket), end="")

    username = input(f"User ({ip}:(none)): ")
    send_cmd(client_socket, f"User {username}")
    resp = get_resp(client_socket)
    print(resp, end="")

    resp_code = resp.split()[0]

    if resp_code == "501": 
        print("Login failed.")
        return
    elif resp_code == "331":
        password = getpass("Password: ")
        client_socket.sendall(f"PASS {password}\r\n".encode())
        resp = client_socket.recv(1024).decode()
        resp_code = resp.split()[0]
        if resp_code == "530":
            print("\n" + resp, end="")
            print("Login failed.")
            return
        elif resp_code == "230":
            print("\n" + resp, end="")
            return
        else:
            print("unexpected error, password")
            return
    else:
        print("unexpected error, user")
        return

def pwd():
    try:
        send_cmd(client_socket, "XPWD")
        print(get_resp(client_socket), end="")
    except:
        print("Not connected.")

def disconnect(mode):
    try:
        send_cmd(client_socket, "QUIT")
        print(get_resp(client_socket), end="")
        close_sock()
    except:
        if mode == 'disconnect' or mode == 'close':
            print("Not connected.")

def close_sock():
    global client_socket
    try:
        client_socket.close()
        client_socket = None
        return
    except:
        client_socket = None
        return

def user(username):
    if not host:
        print("Not connected.")
        return
    if username == None:
        username = input("Username ")

    send_cmd(client_socket, f"USER {username}")
    resp = get_resp(client_socket)
    resp_code = resp.split()[0]

    if resp_code == '503':
        print(resp, end="")
        print("Login failed.")
        return
    elif resp_code == "331":
        print(resp, end="")
        password = getpass("Password: ")
        client_socket.sendall(f"PASS {password}\r\n".encode())
        resp = client_socket.recv(1024).decode()
        resp_code = resp.split()[0]
        if resp_code == "530":
            print("\n" + resp, end="")
            print("Login failed.")
            return
        elif resp_code == "230":
            print("\n" + resp, end="")
            return
        else:
            print("unexpected error, password")
            return


while True:
    line = input('ftp> ').strip()
    args = line.split()
    if args == []:
        continue
    
    command = args[0]
    if len(args) > 1:
        option = args[1:]
    else:
        option = [None]

    if command == 'ascii':
        ascii()

    elif command == 'binary':
        binary()

    elif command == 'bye':
        disconnect('bye')
        break

    elif command == 'cd':
        cd(*option)

    elif command == 'close':
        disconnect('close')

    elif command == 'delete':
        delete(*option)

    elif command == 'disconnect':
        disconnect('disconnect')

    elif command == 'get':
        get(*option)

    elif command == 'ls':
        ls(*option)

    elif command == 'open':
        ftp_open(*option)

    elif command == 'put':
        put(*option)

    elif command == 'pwd':
        pwd()

    elif command == 'quit':
        disconnect('quit')
        break

    elif command == 'rename':
        rename(*option)

    elif command == 'user':
        user(*option)

    elif option[0] == None:
        print("Invalid command.")