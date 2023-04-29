__author__ = 'Agam'

import datetime
import sys
import socket, time
import hashlib
import ssl
import threading, os
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
from sqlCommands import Song
import customtkinter as ctk
import tkinter as tk

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEBUG = True
LOG_ALL = True
TEST = False
token_dict = {}
token_lock = threading.Lock()
UDP_PORT = 5555
TCP_PORT = 7777
TOKEN_PORT = 9999
FILE_PACK_SIZE = 1000
HEADER_SIZE = 9 + 1 + 8 + 1 + 32
LOGGED = False
USERNAME = ''
exit_all = False
CLI_PATH = ''
local_files = {}
SAVED_FILES = False

class App(ctk.CTk):
    def __init__(self,cli_s,cli_path):
        global CLI_PATH
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme('green')
        ctk.CTk.__init__(self)
        self.geometry('1000x1000')
        self._frame = None
        self.cli_s = cli_s
        self.username = ''
        CLI_PATH = cli_path
        self.switch_frame(LoginOrSignUp)



    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        print('switched to ',frame_class)

    def get_cli_socket(self):
        return self.cli_s
    def get_username(self):
        return self.username
    def set_username(self,username):
        self.username=username

class MainApp(ctk.CTkFrame):
    def __init__(self, master):
        self.master=master
        ctk.CTkFrame.__init__(self, master)
        self.cli_s = master.cli_s
        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)

        self.udp_srv = threading.Thread(target=udp_server, args=(CLI_PATH, local_files, exit_all))
        self.udp_srv.start()
        time.sleep(0.3)
        self.token_srv = threading.Thread(target=self.token_server)
        self.token_srv.start()
        time.sleep(0.3)
        self.search_results = None

        self.loop()

    def token_server(self):
        while True:
            data = recv_by_size(self.cli_s)
            if data == "" or exit_all:
                print("seems server DC")
                break
            if len(data) < 8:
                print("seems bad message format:" + data)
                break
            self.data_recv(data)
        return

    def data_recv(self,data):
        global token_dict
        action = data[:8]
        fields = data[9:].split("|")
        if action == 'LOG_BACK':
            if fields[0] == 'OK':
                print('logged!')
            else:
                print('not logged')
        elif action == "SCH_BACK":
            if self.search_results is not None:
                self.search_results.destroy()
            self.search_results = SearchResult(self,fields)

        elif action == "SHR_BACK":
            print("Share status: " + data)

        elif action == "UPD_BACK":
            print("Got " + data)

        elif action == "LNK_BACK":

            fname = fields[0]
            fip = fields[1]
            fsize = int(fields[2])
            ftoken = fields[3]
            if fip != "0.0.0.0":
                print('got to udp client')
                time.sleep(0.5)
                udp_cli = threading.Thread(target=udp_client, args=(CLI_PATH, fip, fname, fsize, ftoken))
                udp_cli.start()
                print("Run udp client to download the file " + fname + " from " + fip)
                udp_cli.join()
            else:
                pass
                # Todo - ask file from server

        elif action == "TKN_BACK":  # server sends to listening client
            token = fields[0]
            start_time = fields[1]
            token_lock.acquire()
            token_dict[token] = start_time
            print(token_dict)
            token_lock.release()
        elif action == 'LGO_BACK':
            self.master.switch_frame(LoginOrSignUp)
        elif action == "RUL_BACK":
            print("Server answer and Live")
        else:
            print("Unknown action back " + action)

    def loop(self):
        global exit_all
        title_label = ctk.CTkLabel(self, text='Welcome to Agamusic!', font=('Arial', 18), text_color='#6DC868')
        title_label.pack(pady=10)
        self.search_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.search_entry.pack(pady=5)
        search_button = ctk.CTkButton(self, text='search', command=self.search)
        search_button.pack(pady=10)
        """logout_button = ctk.CTkButton(self,text ='Logout', command=self.logout)
        logout_button.place(relx=1, rely=0.1, anchor='ne')"""


        while True:
            data = self.manu()

            if data == "q":
                break

            send_with_size(self.cli_s, data)

        self.cli_s.close()
        exit_all = True
        self.udp_srv.join()
        self.token_srv.join()

    def search(self):
        keyword = self.search_entry.get()
        to_send = "SCH|" + keyword
        send_with_size(self.cli_s,to_send)

    def logout(self):
        global LOGGED
        to_send = f'LGO|{USERNAME}'
        send_with_size(self.cli_s,to_send)
        LOGGED =False

    def get_file(self,file_name):
        to_send =  "LNK|" + file_name
        send_with_size(self.cli_s, to_send)

    def manu(self):
        print("\n=============\n" +
              "1. SCH - show server file list\n" +
              "2. SHR - share my files \n" +
              "3. LNK - get file link \n" +
              "4. PLY - play mp3 file\n\n"
              "9. exit\n>" +
              "=============\n\n")

        data = input("Select number > ")

        if data == "9":
            return "q"

        elif data == "2":
            to_send = "SHR|" + str(len(local_files))
            for file, song in local_files.items():
                to_send += f"|{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{USERNAME}~{song.size}"
            return to_send
        elif data == "3":
            fn = input("enter file name>")
            return "LNK|" + fn
        elif data == "4":
            sn = input("enter song file name>")
            # play_song(cli_path, sn)
            return "RULIVE"

        else:
            return "RULIVE"

class LocalFilesFrame(ctk.CTkFrame):
    def __init__(self, master):
        self.files_list = [f for f in os.listdir(CLI_PATH) if os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.mp3')]
        if len(self.files_list) == 0:
            master.switch_frame(MainApp)
            return
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)

        title_label = ctk.CTkLabel(self, text='Add Local Files', font=('Arial', 18))
        title_label.pack(pady=10)

        # Create a table to display the song information
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['File Name', 'Song Name', 'Artist', 'Genre']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=('Arial', 12), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')

        # Get the local files in the directory
        self.files_list = [f for f in os.listdir(CLI_PATH) if os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.mp3')]
        print(self.files_list)
        # Add the rows to the table for each local file
        for i, file_name in enumerate(self.files_list):
            # Create the labels for the file name, song name, artist, and genre
            file_name_label = ctk.CTkLabel(table_frame, text=file_name, font=('Arial', 12), padx=10, pady=5)
            file_name_label.grid(row=i+1, column=0, sticky='w')

            song_name_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            song_name_entry.grid(row=i+1, column=1, sticky='w')

            artist_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            artist_entry.grid(row=i+1, column=2, sticky='w')

            genre_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            genre_entry.grid(row=i+1, column=3, sticky='w')

            # Save the information when the user clicks the save button
            save_button = ctk.CTkButton(table_frame, text='Save', font=('Arial', 12), command=lambda f=file_name, sn=song_name_entry, a=artist_entry, g=genre_entry: self.save_song_info(f, sn.get(), a.get(), g.get()))
            save_button.grid(row=i+1, column=4, padx=10)




    def save_song_info(self,file_name, song_name, artist, genre):
        global local_files, SAVED_FILES
        local_files[file_name] = Song(file_name, song_name, artist, genre, USERNAME,
                    size=os.path.getsize(os.path.join(CLI_PATH, file_name)))
        saved_label = ctk.CTkLabel(self, text=f"{file_name} saved", font=('Arial', 12), padx=10, pady=5)
        saved_label.pack(pady=10)
        if len(local_files)==len(self.files_list):
            SAVED_FILES= True
            self.master.switch_frame(MainApp)


class SearchResult(ctk.CTkFrame):
    def __init__(self, master, fields):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center',relx=0.5,rely=0.8, relheight=0.95,relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Search Results', font=('Arial', 18))
        title_label.pack(pady=10)

        # Create a table to display the search results
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['File Name','Song', 'Artist', 'Genre', 'Size', 'Username', 'Available','Download']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=('Arial', 14), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')

        # Add the search results to the table
        i=1
        for f in fields:
            info = f.split("~")
            if len(info) > 1:
                file_name = ctk.CTkLabel(table_frame, text=info[0], font=('Arial', 14), padx=10, pady=5)
                file_name.grid(row=i + 1, column=0, sticky='w')

                song_label = ctk.CTkLabel(table_frame, text=info[1], font=('Arial', 14), padx=10, pady=5)
                song_label.grid(row=i + 1, column=1, sticky='w')

                artist_label = ctk.CTkLabel(table_frame, text=info[2], font=('Arial', 14), padx=10,pady=5)
                artist_label.grid(row=i + 1, column=2, sticky='w')

                genre_label = ctk.CTkLabel(table_frame, text=info[3], font=('Arial', 14), padx=10, pady=5)
                genre_label.grid(row=i + 1, column=3, sticky='w')

                size_label = ctk.CTkLabel(table_frame, text=info[4], font=('Arial', 14), padx=10,pady=5)
                size_label.grid(row=i + 1, column=4, sticky='w')

                username_label = ctk.CTkLabel(table_frame, text=info[5], font=('Arial', 14),padx=10, pady=5)
                username_label.grid(row=i + 1, column=5, sticky='w')

                available_label = ctk.CTkLabel(table_frame, text=info[6], font=('Arial', 14),padx=10, pady=5)
                available_label.grid(row=i + 1, column=6, sticky='w')
                if info[6] == 'True':
                    print('download is available')
                    download_button = ctk.CTkButton(table_frame, command=lambda f=info[0]: self.master.get_file(f) ,text='Download!')
                else:
                    download_button = ctk.CTkButton(table_frame , text='Unavailable')
                download_button.grid(row=i + 1, column=7, sticky='w')


            else:
                empty_label = ctk.CTkLabel(table_frame,text=f"No search results")
                empty_label.pack(pady=10)
            i+=1


class LoginOrSignUp(ctk.CTkFrame):
    def __init__(self, master):
        self.master=master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)

        self.cli_s = self.master.get_cli_socket()
        title_label = ctk.CTkLabel(self, text='Welcome!', font=('Arial', 18))
        title_label.pack(pady=10)

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12),command=lambda: self.master.switch_frame(Login))
        login_button.pack(pady=10)

        signup_button = ctk.CTkButton(self, text='Sign up', font=('Arial', 12),command=lambda: self.master.switch_frame(Signup))
        signup_button.pack(pady=10)


class Signup(ctk.CTkFrame):
    def __init__(self, master):
        print('got to signup frame')
        ctk.CTkFrame.__init__(self, master)
        self.signed = False
        self.username = ''
        self.cli_s = master.cli_s

        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Sign Up', font=('Arial', 18),text_color='#6DC868')
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=('Arial', 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=('Arial', 12) )
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=('Arial', 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='signup', font=('Arial', 12), command=self.signup)
        login_button.pack(pady=10)

    def signup(self):
        global USERNAME, LOGGED
        while not self.signed:
            self.username = self.username_entry.get()
            password = self.password_entry.get()

            to_send = f'SGN|{self.username}|{password}'
            send_with_size(self.cli_s, to_send)
            result = recv_by_size(self.cli_s)
            if result[-4:] == 'sign':
                self.signed = True
                LOGGED = True
                USERNAME =  self.username
            elif result[-4:] == 'exst':
                tk.messagebox.showerror('Error',
                                        'username already exists or is currently logged, please try a different user')
        if self.signed:
            logging_label = ctk.CTkLabel(self, text='logging in...', font=('Arial', 12))
            logging_label.pack(pady=5)
            self.master.set_username(self.username)
            self.master.switch_frame(LocalFilesFrame)




class Login(ctk.CTkFrame):
    def __init__(self, master):
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        self.logged = False
        self.username = ''
        self.cli_s=master.cli_s

        title_label = ctk.CTkLabel(self, text='Login', font=('Arial', 18))
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=('Arial', 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=('Arial', 12))
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=('Arial', 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12), command=self.login, fg_color='#6DC868')
        login_button.pack(pady=10)


    def login(self):
        global LOGGED, USERNAME
        while not self.logged:
            self.username = self.username_entry.get()
            password = self.password_entry.get()
            to_send = f"LOG|{self.username}|{password}"
            send_with_size(self.cli_s, to_send)

            # Receive authentication result from server
            auth_result = recv_by_size(self.cli_s)
            if auth_result[-2:] == 'OK':
                self.logged = True
                USERNAME = self.username
                LOGGED = True
            elif auth_result == "EXT":
                tk.messagebox.showerror('Error','exceeded maximum tries. Please try to log in later')
                self.destroy()
                break
            else:
                tk.messagebox.showerror('Error', 'invalid username or password!')
                return
        if not self.logged:
           self.username = ''
        else:
            logging_label = ctk.CTkLabel(self, text='logging in...', font=('Arial', 12))
            logging_label.pack(pady=5)
            self.master.set_username(self.username)
            self.master.switch_frame(LocalFilesFrame)



def login(cli_s):
    logged = False
    signed = True
    username = ''
    sign_or_log = input("do you have an account or do you want to sign in? enter 1 to login and 2 to sign up>")
    if sign_or_log == '2':
        signed = False
        while not signed:
            username = input('please enter you new username> ')
            password = input('please enter your new password> ')
            confirm_pass = input('please rewrite your password> ')
            if password == confirm_pass:
                to_send = f'SGN|{username}|{password}'
                send_with_size(cli_s, to_send)
                result = recv_by_size(cli_s)
                if result[-4:] == 'sign':
                    signed = True
                elif result[-4:] == 'exst':
                    print('username already exists or is currently logged, please try a different user')
            else:
                print(' please re-enter your credentials')

    while not logged and signed:
        username = input("please enter your username> ")
        password = input("please enter your password> ")
        # Send username and password to server
        to_send = f"LOG|{username}|{password}"
        send_with_size(cli_s, to_send)

        # Receive authentication result from server
        auth_result = recv_by_size(cli_s)
        if auth_result[-2:] == 'OK':
            logged = True
        if auth_result == "EXT":
            break
    return logged, username


def udp_log(side, message):
    with open("udp_" + side + "_log.txt", 'a') as log:
        log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
        if LOG_ALL:
            print(message)


def manu(username, local_files):
    print("\n=============\n" +
          "1. SCH - show server file list\n" +
          "2. SHR - share my files \n" +
          "3. LNK - get file link \n" +
          "4. PLY - play mp3 file\n\n"
          "9. exit\n>" +
          "=============\n\n")

    data = input("Select number > ")

    if data == "9":
        return "q"
    elif data == "1":
        keyword = input("search for:")
        return "SCH|" + keyword

    elif data == "2":
        to_send = "SHR|" + str(len(local_files))
        for file, song in local_files.items():
            to_send += f"|{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{username}~{song.size}"
        return to_send
    elif data == "3":
        fn = input("enter file name>")
        return "LNK|" + fn
    elif data == "4":
        sn = input("enter song file name>")
        # play_song(cli_path, sn)
        return "RULIVE"

    else:
        return "RULIVE"


def load_local_files(cli_path, username):
    d = {}
    for f in os.listdir(cli_path):
        full_name = os.path.join(cli_path, f)
        if DEBUG:
            print("f " + full_name + " " + str(os.path.isfile(full_name)))
        if os.path.isfile(full_name) and f.endswith(".mp3"):
            d[f] = Song(f, input(f'{f} name: '), input(f'{f} artist: '), input(f'{f} genre: '), username,
                        size=os.path.getsize(full_name))
    return d


def check_valid_token(token):
    global token_dict
    print('got to check token')
    if token in token_dict.keys():
        time_difference = (
                    datetime.datetime.now() - datetime.datetime.strptime(token_dict[token], DATETIME_FORMAT)).seconds
        if time_difference < 7200:  # 2 hours
            token_lock.acquire()
            del token_dict[token]
            token_lock.release()
            return True
    return False


def udp_server(cli_path, local_files, exit_all):
    """
    will get file request and will send Binary file data
    """

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bind_ok = False

    try:
        udp_sock.bind(("0.0.0.0", UDP_PORT))
        bind_ok = True
        print('udp server is up')
    except socket.error as e:
        udp_log("server", " Sock error:" + str(e))
        if e.errno == 10048:
            udp_log("server", "Cant Bind  2 udp servers on same computer")

    while not exit_all and bind_ok:
        try:
            udp_log("server", "Go to listen")
            bin_data, addr = udp_sock.recvfrom(1024)
            data = bin_data.decode()
            if data == "":
                continue
            if DEBUG:
                udp_log("server", " Got UDP Request " + data)
            if data[:3] == "FRQ":
                # print('got request')
                fields = data[4:].split("|")
                fn = fields[0]
                fsize = int(fields[1])
                ftoken = fields[2]
                print(fn, fsize, ftoken)
                if check_valid_token(ftoken):
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
                else:
                    udp_log("server", "invalid token " + ftoken)
        except socket.error as e:
            print("-Sock error:" + str(e.args) + " " + e.message)
            if e.errno == 10048:
                udp_log("server", "Cant Bind  2 udp servers on same computer")
                break
            elif e.errno == 10040:
                udp_log("server", "file too large")
                continue
        except Exception as e:
            udp_log("server", "General error " + str(e))
            break
    udp_sock.close()
    udp_log("server", "udp server off")


def udp_file_send_test(udp_sock, fullname, fsize, addr):
    pos = 0
    done = False
    pack_cnt = 1
    keep = {}
    with open(fullname, 'rb') as f_data:
        while not done:
            bin_data = f_data.read(FILE_PACK_SIZE)
            if len(bin_data) == 0:
                udp_log("server", "Seems empty file in disk" + fullname)
                break
            pos += len(bin_data)
            if pos >= fsize:
                done = True
            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            header = (str(len(bin_data)).zfill(9) + "," + str(pack_cnt).zfill(8) + "," + checksum).encode()
            bin_data = header + bin_data
            keep[pack_cnt] = bin_data
            pack_cnt += 1

    try:
        for k, v in keep.items():
            if k != 2 and k != 3:
                udp_sock.sendto(v, addr)
                if DEBUG and LOG_ALL:
                    pass
                    udp_log("server", "TEST - Just sent part %d file with %d bytes header %s " % (k, len(v), v[:18]))
        udp_sock.sendto(keep[3], addr)
        udp_sock.sendto(keep[2], addr)

        if DEBUG:
            udp_log("server", "TEST - Just sent also 8 5 and 4 ")
    except socket.error as e:
        udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

    if DEBUG:
        udp_log("server", "End of send udp file")


def udp_file_send(udp_sock, fullname, fsize, addr):
    pos = 0
    done = False
    pack_cnt = 1
    with open(fullname, 'rb') as f_data:
        while not done:
            bin_data = f_data.read(FILE_PACK_SIZE)
            if len(bin_data) == 0:
                udp_log("server", "Seems empty file in disk" + fullname)
                break
            pos += len(bin_data)
            if (pos >= fsize):
                done = True

            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            header = (str(len(bin_data)).zfill(9) + "," + str(pack_cnt).zfill(8) + "," + checksum).encode()
            bin_data = header + bin_data
            try:
                udp_sock.sendto(bin_data, addr)
                if DEBUG and LOG_ALL:
                    pass
                    udp_log("server", "Just sent part %d file with %d bytes pos = %d header %s " % (
                        pack_cnt, len(bin_data), pos, bin_data[:18]))
                pack_cnt += 1
            except socket.error as e:
                udp_log("server", "Sock send error: addr = " + addr[0] + ":" + str(addr[1]) + " " + str(e.errno))

    if DEBUG:
        udp_log("server", "End of send udp file")


def udp_file_recv(udp_sock, fullname, size, addr):
    done = False
    file_pos = 0
    last = 0
    max = 0
    keep = {}
    file_open = False
    all_ok = False
    checksum_error = False
    try:

        while not done:
            data = b""
            while len(data) < HEADER_SIZE:
                rcv_data, addr = udp_sock.recvfrom(FILE_PACK_SIZE + HEADER_SIZE)
                if rcv_data == b"":
                    return False
                data += rcv_data
            if data == "":
                return False
            if not file_open:
                f_write = open(fullname, 'wb')
                file_open = True

            header = data[:HEADER_SIZE].decode()
            pack_size = int(header[:9])
            pack_cnt = int(header[10:18])
            pack_checksum = header[19:]
            bin_data = data[HEADER_SIZE:]
            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()
            if checksum != pack_checksum:
                checksum_error = True
                udp_log("client", "Checksum error pack " + str(pack_cnt))
            file_pos += pack_size
            if (file_pos >= size):
                done = True

            if DEBUG and LOG_ALL:
                pass
                udp_log("client", "Just got part %d file with %d bytes pos = %d header %s " % (
                    pack_cnt, len(bin_data), file_pos, header))

            if pack_cnt - 1 == last:
                f_write.write(bin_data)
                last += 1
            else:
                keep[pack_cnt] = bin_data
                if pack_cnt > max:
                    max = pack_cnt
            last = try_to_move_old_packs_to_file(f_write, last, max, keep)
        if file_open:
            f_write.close()
        if done:
            if os.path.isfile(fullname):
                if os.path.getsize(fullname) == size:
                    if not checksum_error:
                        all_ok = True

    except socket.error as e:
        udp_log("client", "Failed to recv: " + str(e.errno))

    if all_ok:
        udp_log("client", "UDP Download  Done " + fullname + " len=" + str(size))
    else:
        udp_log("client", "Something went wrong. cant download " + fullname)


def try_to_move_old_packs_to_file(f_data, last, max, keep):
    to_del = []

    for i in range(last + 1, max + 1):
        if i in keep.keys() and i - 1 == last:
            f_data.write(keep[i])
            last += 1
            to_del.append(i)
            if DEBUG:
                udp_log("client", "----- Wrote old pack %d from dict ---------- " % i)
        else:
            break
    for i in to_del:
        del keep[i]

    return last


def udp_client(cli_path, ip, fn, size, token):
    """
    will send file request and then will recv Binary data
    """
    # print("got to func")
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (ip, UDP_PORT)
    udp_sock.settimeout(10)
    send_ok = False

    to_send = "FRQ|" + fn + "|" + str(size) + "|" + token
    try:

        udp_sock.sendto(to_send.encode(), addr)
        send_ok = True
        if DEBUG:
            udp_log("client", "Sent " + to_send + " to " + addr[0] + " " + str(addr[1]))

    except socket.timeout:
        print("timeout on socket - No answer")
    except socket.error as e:
        if e.errno == 10040:
            udp_log("client", "Send faliled Too large file")
        else:
            udp_log("client", "Send faliled general socket error  " + e.message)

    if send_ok and size > 0:

        udp_file_recv(udp_sock, os.path.join(cli_path, fn), size, addr)

    else:
        if DEBUG:
            udp_log('client', "Send failed or size = 0")
    udp_sock.close()


def data_recv(data, cli_path):
    global token_dict

    action = data[:8]
    fields = data[9:].split("|")
    if action == 'LOG_BACK':
        if fields[0] == 'OK':
            print('logged!')
        else:
            print('not logged')
    elif action == "SCH_BACK":
        print("\n File List")
        for f in fields:
            info = f.split("~")
            if len(info) > 1:
                print("\t{} {} {} {} {}\n".format(info[0], info[1], info[2], info[3], info[4]), end=' ')
            else:
                print("\tserver's directory is empty\n")

    elif action == "SHR_BACK":
        print("Share status: " + data)

    elif action == "UPD_BACK":
        print("Got " + data)

    elif action == "LNK_BACK":
        fname = fields[0]
        fip = fields[1]
        fsize = int(fields[2])
        ftoken = fields[3]
        if fip != "0.0.0.0":
            print('got to udp client')
            udp_cli = threading.Thread(target=udp_client, args=(cli_path, fip, fname, fsize, ftoken))
            udp_cli.start()
            print("Run udp client to download the file " + fname + " from " + fip)
            udp_cli.join()
        else:
            pass
            # Todo - ask file from server

    elif action == "TKN_BACK":  # server sends to listening client
        token = fields[0]
        start_time = fields[1]
        token_lock.acquire()
        token_dict[token] = start_time
        print(token_dict)
        token_lock.release()

    elif action == "RUL_BACK":
        print("Server answer and Live")
    else:
        print("Unknown action back " + action)


def main(cli_path, server_ip):
    print("before connect ip = " + server_ip)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to the server
    client_socket.connect((server_ip, TCP_PORT))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(r'cert\cert.pem')
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    # create a socket and connect to the server
    cli_s = context.wrap_socket(client_socket, server_hostname=server_ip)

    exit_all = False

    logged, username = login(cli_s)
    if not logged:
        return

    local_files = load_local_files(cli_path, username)
    udp_srv = threading.Thread(target=udp_server, args=(cli_path, local_files, exit_all))
    udp_srv.start()
    time.sleep(0.3)
    token_srv = threading.Thread(target=token_server, args=(cli_s, cli_path, exit_all))
    token_srv.start()
    time.sleep(0.3)
    while True:
        data = manu(username, local_files)

        if data == "q":
            break

        send_with_size(cli_s, data)

    cli_s.close()
    exit_all = True
    udp_srv.join()
    token_srv.join()
    print("Main Client -  Bye Bye")


def main_test(cli_path, server_ip):
    print("before connect ip = " + server_ip)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # connect to the server
    client_socket.connect((server_ip, TCP_PORT))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(r'cert\cert.pem')
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    # create a socket and connect to the server
    cli_s = context.wrap_socket(client_socket, server_hostname=server_ip)

    exit_all = False
    username = ''
    app = App(cli_s,cli_path)
    app.mainloop()


if __name__ == "__main__":
    if len(argv) > 2:
        # main(argv[1], argv[2])
        sys.path.append(r"E:\finalProject\venv\Lib\site-packages\customtkinter")
        main_test(argv[1], argv[2])

    else:
        print("USAGE : <enter client folder> <server_ip>")
        exit()
