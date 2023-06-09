__author__ = 'Agam'

import datetime
import secrets
import socket
import ssl
import string
import threading
import time
from sys import argv

import sqlCommands
from tcp_by_size import send_with_size, recv_by_size

TCP_PORT = 8888
DEBUG = True
exit_all = False
songs_database = sqlCommands.SongsORM('server_database.db')
users_database = sqlCommands.UserORM('server_database.db')
files_lock = threading.Lock()
current_tokens = {}
token_lock = threading.Lock()
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
SERVER_IP = ''

class Token():
    def __init__(self, token, start_time):
        self.token = token
        self.start_time = start_time
        self.ack = False
        self.handling = False

    def is_ack(self):
        return self.ack

    def set_ack(self):
        self.ack = True

    def in_handle(self):
        return self.handling

    def set_handle(self):
        self.handling = True

    def __str__(self):
        return self.token + "~" + str(self.start_time)

def create_token():
    """
    creates a 16 chars string that is used for authentication between client's
    :return: a token string
    """
    secure_str = ''.join((secrets.choice(string.ascii_letters + string.digits) for i in range(16)))
    return Token(secure_str, datetime.datetime.now().strftime(DATETIME_FORMAT))


def login(client_socket, cli_ip):
    """
    handles the login/signup process
    :param client_socket: the client's socket
    :param cli_ip: the client's ip
    :return: bool whether the user is logged and the username if they are logged
    """
    tries = 5
    logged = False
    username = ''
    data = recv_by_size(client_socket)

    if data == "":
        print("Error: Seems Client DC")
        return False, ''
    while data[:6] == 'SIGNUP':
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
        if tries != 5:
            data = recv_by_size(client_socket)
        to_send = do_action(data, cli_ip)
        if to_send[-2:] == 'OK':
            logged = True
            username = data.split('|')[1]
        elif tries == 0:
            to_send = "GOODBY"
        send_with_size(client_socket, to_send)
        tries -= 1

    return logged, username


def handle_token(cli_ip, sock):
    """
    the token's thread function that sends a token to the udp server (a tcp client)
     when there is a request from another client
    :param cli_ip: the client's ip
    :param sock: the client's socket
    :return: none
    """
    while True:
        if exit_all:
            print("Seems Server DC")
            break
        if cli_ip in current_tokens.keys() and not current_tokens[cli_ip].in_handle():
            current_tokens[cli_ip].set_handle()
            data = "SENDTK"
            to_send = do_action(data, cli_ip)
            send_with_size(sock, to_send)
            time.sleep(0.5)


def handle_client(sock, tid, cli_ip):
    """
    handles the main communication with the client.
    Receives client's request and sends corrosponding answers
    :param sock: the client's sock
    :param tid: the thread id
    :param cli_ip: the client's ip
    :return: none
    """
    global exit_all
    if exit_all:
        sock.close()
        return
    print("New Client num " + str(tid))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(r'cert\cert.pem', r'cert\key.pem')
    client_socket = context.wrap_socket(sock, server_side=True)

    logged, username = login(client_socket, cli_ip)

    if not logged:
        return
    if DEBUG:
        print(f'user:{username} is logged in from ip:{cli_ip}')
    token_server = threading.Thread(target=handle_token, args=(cli_ip, client_socket))
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
                login(client_socket, cli_ip)

        except socket.error as err:
            if err.errno == 10054:
                # 'Connection reset by peer'
                print(f"connection reset by client {cli_ip}. loging out user: {username}")
                users_database.logout(username)
                break
            else:
                print("%d General Sock Error Client %s disconnected" % (err.errno, str(client_socket)))
                users_database.logout(username)
                break

        except Exception as err:
            print("General Error:", err)
            break

    token_server.join()
    users_database.logout(username)
    sock.close()


def do_action(data, cli_ip):
    """
    gets the data from client and fills an answer to the client
    :param data: the data recieved from client
    :param cli_ip: the client's ip
    :return: answer to client
    """
    global files_lock, current_tokens, token_lock

    to_send = ''

    try:
        action = data[:6]
        data = data[7:]
        fields = data.split('|')

        if DEBUG:
            print("Got client request " + action + " -- " + str(fields))

        if action == "LOGINC":
            username = fields[0]
            password = fields[1]
            verify = users_database.login(username, password, cli_ip)
            if verify:
                to_send = 'LOGGED' + "|" + "OK"
            else:
                to_send = 'LOGGED' + "|" + "NO"
        elif action == "SIGNUP":
            username = fields[0]
            password = fields[1]
            valid, msg = users_database.signup(username, password, cli_ip)
            to_send = 'SIGNED' + "|" + msg

        elif action == "SEARCH":
            answer = 'SRCHBK'
            songs = songs_database.search_songs(fields[0])
            if len(songs) == 0:
                answer += ''
            else:
                for song in songs:
                    is_available = users_database.is_available(song.md5, fields[1])
                    print('is available ', is_available)
                    answer += f"|{song.md5}~{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{song.size}~" \
                              f"{song.committed_user}~{is_available}"
            to_send = answer

        elif action == "UPLOAD":
            files_lock.acquire()
            songs_database.add_client_folder(fields, cli_ip)
            files_lock.release()
            to_send = "UPLDBK" + "|OK"

        elif action == "LINKFN":
            md5 = fields[0]
            exists = songs_database.song_exists(md5)
            if exists:
                song = songs_database.get_song_by_md5(md5)[0]
                token_obj = create_token()
                if song.ip == SERVER_IP:
                    ip = '127.0.0.1'
                else:
                    ip = song.ip
                token_lock.acquire()
                current_tokens[ip] = token_obj
                token_lock.release()
                while not current_tokens[ip].is_ack():
                    time.sleep(0.01)

                print('token acknowledged')
                print("song's ip: ",ip)
                if song.ip == '127.0.0.1':
                    ip = SERVER_IP
                else:
                    ip = song.ip
                time.sleep(0.3)
                to_send = f'LINKBK|{song.file_name}|{ip}|{song.size}|{token_obj.token}|{song.song_name}|' \
                          f'{song.artist}|{song.genre}|{song.md5}'
                token_lock.acquire()
                del current_tokens[ip]
                token_lock.release()
            else:
                to_send = handle_error(4)

        elif action == 'SENDTK':
            token = current_tokens[cli_ip]
            to_send = f'SENDTK|{token.token}|{token.start_time}'

        elif action == 'TOKACK':
            token_lock.acquire()
            current_tokens[cli_ip].set_ack()
            token_lock.release()
            print(f'{cli_ip} got token')
            to_send = 'AMLIVE' + "|Server Is Live"

        elif action == "RULIVE":
            to_send = 'AMLIVE' + "|Server Is Live"
        else:
            print("Got unknown action from client " + action)
            to_send = handle_error(2)
    except Exception as e:
        print(e)
        to_send = handle_error(1)
    return to_send


def handle_error(error_num):
    """
    gets an error code and returns the answer to client
    :param error_num: the error code number
    :return: error answer to client
    """
    to_send = "ERRORS|"
    if error_num == 1:
        to_send += "001|General Exception"
    elif error_num == 2:
        to_send += "002|Unknown Action"
    elif error_num == 3:
        to_send += "003|SSL Error"
    elif error_num == 4:
        to_send += "004|File Not Found"
    return to_send


def main():
    """
    the main loop of the server. Opens a TCP socket handles the threading process of clients
    :return:
    """
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
    users_database.logout_all()

    s.close()


if __name__ == "__main__":
    if len(argv) == 2:
        SERVER_IP = argv[1]
        main()
    else:
        print("USAGE : <enter your IP>")
        exit()
