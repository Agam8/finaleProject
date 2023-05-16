__author__ = 'Agam'

import socket
import ssl
import queue, threading, time, datetime
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
import secrets
import string
import sqlCommands
from token_config import Token
TCP_PORT=8888
DEBUG = True
exit_all = False
songs_database = sqlCommands.SongsORM('server_database.db')
users_database = sqlCommands.UserORM('server_database.db')
files_lock = threading.Lock()
current_tokens = {}
token_lock = threading.Lock()
DATETIME_FORMAT='%Y-%m-%d %H:%M:%S'
SERVER_IP = '10.0.0.26' #for testing

def create_token():
    secure_str = ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(16)))
    return Token(secure_str,datetime.datetime.now().strftime(DATETIME_FORMAT))

def login(client_socket,cli_ip):
    tries = 5
    logged = False
    username=''
    data = recv_by_size(client_socket)

    if data == "":
        print("Error: Seems Client DC")
        return False,''
    while data[:3] == 'SGN':
        if data == "":
            print("Error: Seems Client DC")
            return False, ''
        to_send = do_action(data, cli_ip)
        send_with_size(client_socket, to_send)
        data = recv_by_size(client_socket)

    while not logged:
        if data == "":
            print("Error: Seems Client DC")
            return False, ''
        if tries!=5:
            data = recv_by_size(client_socket)
        to_send = do_action(data,cli_ip)
        if to_send[-2:] == 'OK':
            logged = True
            username = data.split('|')[1]
        elif tries == 0:
            to_send = "GOODBY"
        send_with_size(client_socket, to_send)
        tries -= 1

    return logged, username


def handle_token(cli_ip,sock):
    while True:
        if exit_all:
            print("Seems Server DC")
            break
        if cli_ip in current_tokens.keys():
            data = "SENDTK"
            to_send = do_action(data, cli_ip)
            send_with_size(sock, to_send)


def handle_client(sock, tid, cli_ip):
    global exit_all
    if exit_all:
        sock.close()
        return
    print("New Client num " + str(tid))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(r'cert\cert.pem', r'cert\key.pem')
    client_socket = context.wrap_socket(sock, server_side=True)

    logged, username= login(client_socket, cli_ip)

    if not logged:
        return
    if DEBUG:
        print(f'user:{username} is logged in from ip:{cli_ip}')
    token_server = threading.Thread(target=handle_token,args=(cli_ip,client_socket))
    token_server.start()
    time.sleep(0.3)

    while not exit_all:
        try:
            data = recv_by_size(client_socket)
            if data == "":
                print("Error: Seems Client DC")
                users_database.logout(username)
                break

            to_send = do_action(data, cli_ip)
            send_with_size(client_socket, to_send)
            if to_send == 'LGO_BACK':
                login(client_socket,cli_ip)

        except socket.error as err:
            if err.errno == 10054:
                # 'Connection reset by peer'
                print("Error %d Client is Gone. %s reset by peer." % (err.errno, str(client_socket)))
                break
            else:
                print("%d General Sock Error Client %s disconnected" % (err.errno, str(client_socket)))
                break

        except Exception as err:
            print("General Error:", err)
            break
    token_server.join()
    users_database.logout(username)
    sock.close()


def do_action(data, cli_ip):
    """
     what client ask and fill to send with the answer
    """
    global files_lock, current_tokens, token_lock

    to_send = "Not Set Yet"

    try:

        action = data[:6]
        data = data[7:]
        fields = data.split('|')

        if DEBUG:
            print("Got client request " + action + " -- " + str(fields))

        if action == "LOGINC":
            username = fields[0]
            password = fields[1]
            verify = users_database.login(username,password,cli_ip)
            if verify:
                to_send = 'LOGGED' + "|"+"OK"
            else:
                to_send = 'LOGGED'+ "|"+"NO"
        elif action == "SIGNUP":
            username = fields[0]
            password = fields[1]
            valid, msg = users_database.signup(username,password,cli_ip)
            to_send = 'SIGNED' + "|"+msg
        elif action == "SEARCH":
            answer = 'SRCHBK'
            print('getting songs')
            songs = songs_database.search_songs(fields[0])
            if len(songs) == 0:
                answer += ''
            else:
                for song in songs:
                    is_available = users_database.is_available(song.md5,fields[1])
                    username = songs_database.get_user_by_song(song.md5)
                    answer += f"|{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{song.size}~{username}~{is_available}~{song.md5}"
            to_send = answer

        elif action == "UPLOAD":
            files_lock.acquire()
            songs_database.add_client_folder(fields, cli_ip)
            files_lock.release()
            to_send = "UPLDBK" + "|OK"

        elif action == "LINKFN":
            md5 = fields[0]
            exists = songs_database.song_exists(md5)
            # print('THIS SONG EXISTS', exists)
            if exists:
                song = songs_database.get_song_by_md5(md5)[0]

                token_obj = create_token()
                token_lock.acquire()
                if song.ip == SERVER_IP:
                    current_tokens['127.0.0.1'] = token_obj
                else:
                    current_tokens[song.ip] = token_obj
                token_lock.release()
                to_send = f'LINKBK|{fn}|{song.ip}|{song.size}|{token_obj.token}|{song.song_name}|{song.artist}|{song.genre}|{song.md5}' # file name, ip, size
            else:
                to_send = "Err___R|File not exist in srv list"

        elif action == 'SENDTK':
            token = current_tokens[cli_ip]
            token_lock.acquire()
            del current_tokens[cli_ip]
            token_lock.release()
            to_send = f'SENDTK|{token.token}|{token.start_time}'

        elif action == "RULIVE":
            to_send = 'AMLIVE' + "|Server Is Live"
        else:
            print("Got unknown action from client " + action)
            to_send = "ERR___R|001|" + "unknown action"
    except Exception as e:
        to_send = "Err___R|do Action General exception "
    return to_send


def load_files_from_server_folder(srv_path):
    """

    :param srv_path:
    :return:
    """
    global songs_database
    songs_database.add_server_folder(srv_path)


def main():
    global exit_all
    exit_all = False
    s = socket.socket()
    s.bind(("0.0.0.0", TCP_PORT))
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
        if i == 10:
            break

    exit_all = True
    for s, t in clients.items():
        t.join()
    # manager.join()
    users_database.logout_all()

    s.close()


if __name__ == "__main__":
    main()
