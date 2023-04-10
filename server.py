import socket
import threading
import os
import datetime
import sqlCommands as sql
from tcp_by_size import *
DEBUG = True
LOG_ALL = False

def udp_log(side, message):
    with open("udp_" + side + "_log.txt", 'a') as log:
        log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
        if LOG_ALL:
            print(message)

def udp_server(cli_path, local_files, exit_all):
    """
    will get file request and will send Binary file data
    """
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bind_ok = False

    try:
        udp_sock.bind(("0.0.0.0", 5501))
        bind_ok = True
    except socket.error as e:
        udp_log("server", " Sock error:" + str(e.args))
        if e.errno == 10048:
            udp_log("server", "Cant Bind  2 udp servers on same computer")

    while not exit_all and bind_ok:
        try:
            udp_log("server", "Go to listen")
            data, addr = udp_sock.recvfrom(1024)
            if data == "":
                continue
            if DEBUG:
                udp_log("server", " Got UDP Request " + data.decode())
            if data[:3] == "FRQ":
                fields = data[4:].split(b"|")
                fn = fields[0]
                fsize = int(fields[1])

            if fn in local_files.keys():
                if local_files[fn].size == fsize and fsize > 0:
                    fullname = os.path.join(cli_path, fn)

                    if TEST:
                        udp_file_send_test(udp_sock, fullname, fsize, addr)
                    else:
                        udp_file_send(udp_sock, fullname, fsize, addr)
                    time.sleep(5)
                else:
                    udp_log("server", "sizes not ok")
            else:
                udp_log("server", "file not found " + fn)
        except socket.error as e:
            print("-Sock error:" + str(e.args) + " " + e.message)
            if e.errno == 10048:
                udp_log("server", "Cant Bind  2 udp servers on same computer")
                break
            elif e.errno == 10040:
                udp_log("server", "file too large")
                continue
        except Exception as e:
            udp_log("server", "General error " + str(e.message))
            break
    udp_sock.close()
    udp_log("server", "udp server off")





def do_action(data):
    to_send=''
    try:
        action = data[:3]
        data = data[4:]
        fields = data.split('|')
def handle_client(sock, tid, files, cli_ip):
    global exit_all
    print("New Client num " + str(tid))

    while not exit_all:
        try:
            data = recv_by_size(sock)
            if data == "":
                print("Error: Seens Client DC")
                break

            to_send = do_action(data, files, cli_ip)

            send_with_size(sock, to_send)

        except socket.error as err:
            if err.errno == 10054:
                # 'Connection reset by peer'
                print("Error %d Client is Gone. %s reset by peer." % (err.errno, str(sock)))
                break
            else:
                print("%d General Sock Error Client %s disconnected" % (err.errno, str(sock)))
                break

        except Exception as err:
            print("General Error:", err)
            break
    sock.close()

def load_files_from_server_folder(srv_path):
    d = {}

    for f in os.listdir(srv_path):
        full_name = os.path.join(srv_path, f)
        if DEBUG:
            print("f " + full_name + " " + str(os.path.isfile(full_name)))
        if os.path.isfile(full_name):
            d[f] = sql.SongsORM(f, os.path.getsize(full_name),)

    return d

def main(srv_path):
    global exit_all
    exit_all = False


    files = load_files_from_server_folder(srv_path)

    s = socket.socket()
    s.bind(("0.0.0.0", 5500))
    s.listen(4)
    print("after listen")

    clients = {}
    i = 1
    while True:
        cli_s, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(cli_s, i, files, addr[0]))
        t.start()
        i += 1

        clients[cli_s] = t
        if i == 5:
            break

    exit_all = True
    for s, t in clients.items():
        t.join()
    manager.join()

    s.close()
