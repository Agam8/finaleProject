__author__ = 'Yossi'

import socket
import os
import queue, threading, time, datetime
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
from Shared_file import Shared_file
from uuid import uuid4

DEBUG = True
exit_all = False

files_lock = threading.Lock()

def create_token(file_name, files):
    token = str(uuid4())
    now = datetime.datetime.now()
    expiry_time = now + datetime.timedelta(hours=2)
    files_lock.acquire()
    if file_name in files:
        files[file_name].token = token
        files[file_name].expiry_time = expiry_time
        files_lock.release()
        return token
    files_lock.release()
    return None



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

def do_action(data, files, cli_ip):
    """
     what client ask and fill to send with the answer
    """
    global files_lock

    to_send = "Not Set Yet"

    try:

        action = data[:3]
        data = data[4:]
        fields = data.split('|')

        if DEBUG:
            print("Got client request " + action + " -- " + str(fields))
        answer = action + "_BACK"

        if action == "DIR":
            for k, v in files.items():
                answer += "|" + str(v)
            to_send = answer

        elif action == "SHR":
            length = int(fields[0])
            print("Got %d files" % length)
            files_lock.acquire()

            for i in range(length):
                info = fields[i + 1].split("~")

                if info[0] not in files.keys():
                    files[info[0]] = Shared_file(info[0], info[1], cli_ip)
                    if DEBUG:
                        print("got new file" + str(files[info[0]]))
                else:
                    print("file already exist " + info[0])
            files_lock.release()
            print("Len of files" + str(len(files)))
            to_send = answer + "|Ok"
        elif action == "LNK":
            fn = fields[0]
            if fn in files.keys():
                to_send = answer + "|" + fn + "|" + files[fn].ip + "|" + str(files[fn].size)
            else:
                to_send = "Err___R|File not exist in srv list"
        elif action == "RUL":
            to_send = answer + "|Server Is Live"
        else:
            print("Got unknown action from client " + action)
            to_send = "ERR___R|001|" + "unknown action"
    except Exception as e:
        to_send = "Err___R|do Action General exception "
    return to_send


def q_manager(tid, q, files):
    global exit_all

    print("manager start:" + str(tid))
    while not exit_all:
        item = q.get()
        print("manager got somthing:" + str(item))
        # do some work with it(item)
        q.task_done()
        time.sleep(0.3)
    print("Manager say Bye")


def load_files_from_server_folder(srv_path):
    d = {}

    for f in os.listdir(srv_path):
        full_name = os.path.join(srv_path, f)
        if DEBUG:
            print("f " + full_name + " " + str(os.path.isfile(full_name)))
        if os.path.isfile(full_name):
            d[f] = Shared_file(f, os.path.getsize(full_name), "0.0.0.0")

    return d


def main(srv_path):
    global exit_all
    exit_all = False

    q = queue.Queue()
    manager = threading.Thread(target=q_manager, args=(0, q, srv_path))

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


if __name__ == "__main__":
    if len(argv) >= 2:
        main(argv[1])
    else:
        main('server_files')
