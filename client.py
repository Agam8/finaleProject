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
import playsound

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEBUG = True
LOG_ALL = True
token_dict = {}
token_lock = threading.Lock()
UDP_PORT = 7777
TCP_PORT = 8888
FILE_PACK_SIZE = 1000
HEADER_SIZE = 9 + 1 + 8 + 1 + 32
LOGGED = False
USERNAME = ''
exit_all = False
CLI_PATH = ''
local_files = {}
SAVED_FILES = False


class App(ctk.CTk):
    def __init__(self, cli_s, cli_path):
        global CLI_PATH
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme('green')
        ctk.CTk.__init__(self)
        self.geometry('900x900')
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
        print('switched to ', frame_class)

    def get_cli_socket(self):
        return self.cli_s

    def get_username(self):
        return self.username

    def set_username(self, username):
        self.username = username


class MainApp(ctk.CTkFrame):
    def __init__(self, master):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.cli_s = master.cli_s
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        self.udp_srv = threading.Thread(target=udp_server, args=(CLI_PATH, local_files, exit_all))
        self.udp_srv.start()
        time.sleep(0.3)
        self.recv_thread = threading.Thread(target=self.recv_thread_func)
        self.recv_thread.start()
        time.sleep(0.3)
        self.search_results = None
        self.files_frame = None
        self.loop()

    def recv_thread_func(self):
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

    def data_recv(self, data):
        global token_dict
        action = data[:6]
        fields = data[7:].split("|")
        if action == 'LOGGED':
            if fields[0] == 'OK':
                print('logged!')
            else:
                print('not logged')

        elif action == "SRCHBK":
            if self.search_results is not None:
                self.search_results.destroy()
            self.search_results = SearchResult(self, fields)

        elif action == "UPLDBK":
            print("Share status: " + fields[0])

        elif action == "UPD_BACK":
            print("Got " + data)

        elif action == "LINKBK":
            fname = fields[0]
            fip = fields[1]
            fsize = int(fields[2])
            ftoken = fields[3]
            song_name = fields[4]
            artist = fields[5]
            genre = fields[6]

            time.sleep(0.5)
            udp_cli = threading.Thread(target=udp_client,
                                       args=(CLI_PATH, fip, fname, fsize, ftoken, song_name, artist, genre))
            udp_cli.start()
            # print("Run udp client to download the file " + fname + " from " + fip)
            udp_cli.join()

        elif action == "SENDTK":  # server sends to listening client
            token = fields[0]
            start_time = fields[1]
            token_lock.acquire()
            token_dict[token] = start_time
            print(token_dict)
            token_lock.release()
            print('added-- ', token, " --to dict")

        elif action == "AMLIVE":
            print("Server answer and Live")
        else:
            print("Unknown action back " + action)

    def loop(self):
        global exit_all
        self.share_files()
        title_label = ctk.CTkLabel(self, text='Welcome to Agamusic!', font=('Arial', 18), text_color='#6DC868')
        title_label.pack(pady=10)
        self.search_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.search_entry.pack(pady=5)

        search_button = ctk.CTkButton(self, text='search', command=self.search)
        search_button.pack(pady=10)

        my_dir_button = ctk.CTkButton(self, text='My Directory', command=self.show_library)
        my_dir_button.pack(pady=10)

        while True:
            data = self.manu()

            if data == "q":
                break

            send_with_size(self.cli_s, data)

        self.cli_s.close()
        exit_all = True
        self.udp_srv.join()
        self.recv_thread.join()

    def show_library(self):
        if self.files_frame is not None:
            self.files_frame.destroy()
        self.library = ShowLibrary(self)

    def search(self):
        keyword = self.search_entry.get()
        to_send = "SEARCH|" + keyword
        send_with_size(self.cli_s, to_send)

    def get_file(self, file_name):
        to_send = "LINKFN|" + file_name
        send_with_size(self.cli_s, to_send)

    def share_files(self):
        to_send = "UPLOAD|" + str(len(local_files))
        for file, song in local_files.items():
            to_send += f"|{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{USERNAME}~{song.size}"
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


class ShowLibrary(ctk.CTkFrame):
    def __init__(self, master):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.8, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='My Library', font=('Arial', 18))
        title_label.pack(pady=10)

        # Create a table to display the song information
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['File Name', 'Song', 'Artist', 'Genre', 'Play']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=('Arial', 14), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')
        i = 0
        for song in local_files.values():

            file_name = ctk.CTkLabel(table_frame, text=song.file_name, font=('Arial', 14), padx=10, pady=5)
            file_name.grid(row=i + 1, column=0, sticky='w')

            song_label = ctk.CTkLabel(table_frame, text=song.song_name, font=('Arial', 14), padx=10, pady=5)
            song_label.grid(row=i + 1, column=1, sticky='w')

            artist_label = ctk.CTkLabel(table_frame, text=song.artist, font=('Arial', 14), padx=10, pady=5)
            artist_label.grid(row=i + 1, column=2, sticky='w')

            genre_label = ctk.CTkLabel(table_frame, text=song.genre, font=('Arial', 14), padx=10, pady=5)
            genre_label.grid(row=i + 1, column=3, sticky='w')

            play_button = ctk.CTkButton(table_frame, command=lambda f=file_name: self.play_song(os.path.join(CLI_PATH, song.file_name)), text='Play')
            play_button.grid(row=i + 1, column=7, sticky='w')
            i += 1

    def play_song(self, fullname):
        progress_bar=None
        try:
            progress_bar = ctk.CTkProgressBar(self,determinate_speed=0.2)
            progress_bar.place(relx=0.4, rely=0.6)
            progress_bar.start()
            playsound.playsound(fullname)
            print('playing ',fullname)
        except Exception as e:
            print(e)
        print('exiting')
        progress_bar.stop()
        progress_bar.destroy()


class LocalFiles(ctk.CTkFrame):
    def __init__(self, master):
        print('got to local files')
        self.files_list = [f for f in os.listdir(CLI_PATH) if
                           os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.mp3')]
        print(self.files_list)
        if len(self.files_list) == 0:
            print('len is 0')
            master.switch_frame(MainApp)
            print('switched to main')
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
        self.files_list = [f for f in os.listdir(CLI_PATH) if
                           os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.mp3')]
        print(self.files_list)
        # Add the rows to the table for each local file
        for i, file_name in enumerate(self.files_list):
            # Create the labels for the file name, song name, artist, and genre
            file_name_label = ctk.CTkLabel(table_frame, text=file_name, font=('Arial', 12), padx=10, pady=5)
            file_name_label.grid(row=i + 1, column=0, sticky='w')

            song_name_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            song_name_entry.grid(row=i + 1, column=1, sticky='w')

            artist_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            artist_entry.grid(row=i + 1, column=2, sticky='w')

            genre_entry = ctk.CTkEntry(table_frame, font=('Arial', 12))
            genre_entry.grid(row=i + 1, column=3, sticky='w')

            # Save the information when the user clicks the save button
            save_button = ctk.CTkButton(table_frame, text='Save', font=('Arial', 12),
                                        command=lambda f=file_name, sn=song_name_entry, a=artist_entry,
                                                       g=genre_entry: self.save_song_info(f, sn.get(), a.get(),
                                                                                          g.get()))
            save_button.grid(row=i + 1, column=4, padx=10)

        continue_button = ctk.CTkButton(self, text='Continue', font=('Arial', 12), command=self.continue_to_main)
        continue_button.place(relx=0.4,rely=0.7)

    def save_song_info(self, file_name, song_name, artist, genre):
        global local_files, SAVED_FILES
        if file_name not in local_files.keys() and song_name != '' and artist != '' and genre != '':
            local_files[file_name] = Song(file_name, song_name, artist, genre, USERNAME,
                                          size=os.path.getsize(os.path.join(CLI_PATH, file_name)))
            saved_label = ctk.CTkLabel(self, text=f"{file_name} saved", font=('Arial', 12), padx=10, pady=5)
            saved_label.pack(pady=10)
        else:
            not_saved_label = ctk.CTkLabel(self, text=f"{file_name} already saved", font=('Arial', 12), padx=10, pady=5)
            not_saved_label.pack(pady=10)

    def continue_to_main(self):
        if len(local_files) == len(self.files_list):
            SAVED_FILES = True
            self.master.switch_frame(MainApp)
        else:
            no_cont_label = ctk.CTkLabel(self, text="Please save all files before continue", font=('Arial', 12),
                                         padx=10, pady=5)
            no_cont_label.place(relx=0.5, rely=0.9)


class SearchResult(ctk.CTkFrame):
    def __init__(self, master, fields):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.8, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Search Results', font=('Arial', 18))
        title_label.pack(pady=10)

        # Create a table to display the search results
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        if len(fields) == 0:
            empty_label = ctk.CTkLabel(table_frame, text=f"No search results")
            empty_label.pack(pady=10)
            return

        headers = ['File Name', 'Song', 'Artist', 'Genre', 'Size', 'Username', 'Available', 'Download']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=('Arial', 14), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')

        # Add the search results to the table
        i = 1
        for f in fields:
            info = f.split("~")
            file_name = ctk.CTkLabel(table_frame, text=info[0], font=('Arial', 14), padx=10, pady=5)
            file_name.grid(row=i + 1, column=0, sticky='w')

            song_label = ctk.CTkLabel(table_frame, text=info[1], font=('Arial', 14), padx=10, pady=5)
            song_label.grid(row=i + 1, column=1, sticky='w')

            artist_label = ctk.CTkLabel(table_frame, text=info[2], font=('Arial', 14), padx=10, pady=5)
            artist_label.grid(row=i + 1, column=2, sticky='w')

            genre_label = ctk.CTkLabel(table_frame, text=info[3], font=('Arial', 14), padx=10, pady=5)
            genre_label.grid(row=i + 1, column=3, sticky='w')

            size_label = ctk.CTkLabel(table_frame, text=info[4], font=('Arial', 14), padx=10, pady=5)
            size_label.grid(row=i + 1, column=4, sticky='w')

            username_label = ctk.CTkLabel(table_frame, text=info[5], font=('Arial', 14), padx=10, pady=5)
            username_label.grid(row=i + 1, column=5, sticky='w')

            available_label = ctk.CTkLabel(table_frame, text=info[6], font=('Arial', 14), padx=10, pady=5)
            available_label.grid(row=i + 1, column=6, sticky='w')
            if info[6] == 'True':
                print('download is available')
                download_button = ctk.CTkButton(table_frame, command=lambda f=info[0]: self.master.get_file(f),
                                                text='Download!')
            else:
                download_button = ctk.CTkButton(table_frame, text='Unavailable')
            download_button.grid(row=i + 1, column=7, sticky='w')

            i += 1


class LoginOrSignUp(ctk.CTkFrame):
    def __init__(self, master):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)

        self.cli_s = self.master.get_cli_socket()
        title_label = ctk.CTkLabel(self, text='Welcome!', font=('Arial', 18))
        title_label.pack(pady=10)

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12),
                                     command=lambda: self.master.switch_frame(Login))
        login_button.pack(pady=10)

        signup_button = ctk.CTkButton(self, text='Sign up', font=('Arial', 12),
                                      command=lambda: self.master.switch_frame(Signup))
        signup_button.pack(pady=10)


class Signup(ctk.CTkFrame):
    def __init__(self, master):
        print('got to signup frame')
        ctk.CTkFrame.__init__(self, master)
        self.signed = False
        self.username = ''
        self.cli_s = master.cli_s

        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Sign Up', font=('Arial', 18), text_color='#6DC868')
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=('Arial', 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=('Arial', 12))
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=('Arial', 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='signup', font=('Arial', 12), command=self.signup_user)
        login_button.pack(pady=10)

    def signup_user(self):
        global USERNAME, LOGGED
        while not self.signed:
            self.username = self.username_entry.get()
            password = self.password_entry.get()

            to_send = f'SIGNUP|{self.username}|{password}'
            send_with_size(self.cli_s, to_send)
            result = recv_by_size(self.cli_s)
            if result[-2:] == 'OK':
                self.signed = True
                LOGGED = True
                USERNAME = self.username
            elif result[-2:] == 'NO':
                tk.messagebox.showerror('Error',
                                        'username already exists or is currently logged, please try a different user')
        if self.signed:
            logging_label = ctk.CTkLabel(self, text='logging in...', font=('Arial', 12))
            logging_label.pack(pady=5)
            self.master.set_username(self.username)
            self.master.switch_frame(LocalFiles)


class Login(ctk.CTkFrame):
    def __init__(self, master):
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        self.logged = False
        self.username = ''
        self.cli_s = master.cli_s

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

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12), command=self.login_user,
                                     fg_color='#6DC868')
        login_button.pack(pady=10)

    def login_user(self):
        global LOGGED, USERNAME
        while not self.logged:
            self.username = self.username_entry.get()
            password = self.password_entry.get()
            to_send = f"LOGINC|{self.username}|{password}"
            send_with_size(self.cli_s, to_send)

            # Receive authentication result from server
            auth_result = recv_by_size(self.cli_s)
            if auth_result[-2:] == 'OK':
                self.logged = True
                USERNAME = self.username
                LOGGED = True
                print('logging in')
            elif auth_result == "GOODBY":
                tk.messagebox.showerror('Error', 'exceeded maximum tries. Please try to log in later')
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
            self.master.switch_frame(LocalFiles)


def udp_log(side, message):
    with open("udp_" + side + "_log.txt", 'a') as log:
        log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
        if LOG_ALL:
            print(message)


def check_valid_token(token):
    global token_dict
    print('got to check token')
    time.sleep(0.3)
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


def udp_client(cli_path, ip, fn, size, token, song_name, artist, genre):
    """
    will send file request and then will recv Binary data
    """
    # print("got to func")
    global local_files
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
        saved = udp_file_recv(udp_sock, os.path.join(cli_path, fn), size, addr)
        if saved:
            local_files[fn] = Song(fn, song_name, artist, genre, USERNAME, size=size)

    else:
        if DEBUG:
            udp_log('client', "Send failed or size = 0")
    udp_sock.close()


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
            last = move_old_to_file(f_write, last, max, keep)
        if file_open:
            f_write.close()
        if done:
            if os.path.isfile(fullname):
                if os.path.getsize(fullname) == size:
                    if not checksum_error:
                        all_ok = True

    except socket.error as e:
        udp_log("client", "Failed to recv: " + str(e.errno) + str(e))
        return False

    if all_ok:
        udp_log("client", "UDP Download  Done " + fullname + " len=" + str(size))
        return True
    else:
        udp_log("client", "Something went wrong. cant download " + fullname)
        return False


def move_old_to_file(f_data, last, max, keep):
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
    app = App(cli_s, cli_path)
    app.mainloop()


if __name__ == "__main__":
    if len(argv) > 2:
        sys.path.append(r"E:\finalProject\venv\Lib\site-packages\customtkinter")
        main(argv[1], argv[2])

    else:
        print("USAGE : <enter client folder> <server_ip>")
        exit()
