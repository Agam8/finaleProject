__author__ = 'Yossi'

import socket
import os
import queue, threading, time, datetime
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
from Shared_file import Shared_file
from uuid import uuid4
import sqlCommands

DEBUG = True
exit_all = False
songs_database = sqlCommands.SongsORM('server_database.db')
files_lock = threading.Lock()

"""
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
"""


def handle_client(sock, tid, cli_ip):
    global exit_all
    print("New Client num " + str(tid))
    while not exit_all:
        try:
            data = recv_by_size(sock)
            if data == "":
                print("Error: Seens Client DC")
                break

            to_send = do_action(data, cli_ip)

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

def do_action(data, cli_ip):
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
            songs = songs_database.get_all_songs()
            for song in songs:
                answer += "{}~{}~{}~{}~{}~{}".format("|" + song[0], song[1], song[2], song[3], song[4], song[5])
            to_send = answer

        elif action == "SHR":
            files_lock.acquire()
            songs_database.add_client_folder(fields, cli_ip)
            files_lock.release()
            to_send = answer + "|Ok"
        elif action == "LNK":
            fn = fields[0]
            exists = songs_database.song_exists(fn)
            if exists:
                song = songs_database.get_songs_by_name(fn)
                to_send = answer + "|" + fn + "|" + song[4] + "|" + song[5] # file name, ip, size
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


def q_manager(tid, q):
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
    global songs_database
    songs_database.add_server_folder(srv_path)

def main(srv_path):
    global exit_all
    exit_all = False

    q = queue.Queue()
    manager = threading.Thread(target=q_manager, args=(0, q, srv_path))

    load_files_from_server_folder(srv_path)

    s = socket.socket()
    s.bind(("0.0.0.0", 5500))
    s.listen(4)
    print("after listen")

    clients = {}
    i = 1
    while True:
        cli_s, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(cli_s, i, addr[0]))
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
