__author__ = 'Agam'

import datetime
import sys
import socket, time
import hashlib
import ssl
import threading, os
from tcp_by_size import send_with_size, recv_by_size
from sys import argv
from objects import Song
import customtkinter as ctk
import tkinter as tk
from PIL import Image
import wave
import pyaudio

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DEBUG = True
LOG_ALL = True
token_dict = {}
token_lock = threading.Lock()
play_lock = threading.Lock()
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
FONT = 'Yu Gothic UI'
error_handler = None


class App(ctk.CTk):
    def __init__(self, cli_s, cli_path):
        """
        initiating the main ctk.ctk screen
        :param cli_s: client's socket
        :param cli_path: client's path to local shared folder
        """
        global CLI_PATH, error_handler
        ctk.CTk.__init__(self)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme('green')
        self.title('Agamusic')
        self.geometry('900x900')
        self._frame = None
        self.cli_s = cli_s
        CLI_PATH = cli_path
        self.switch_frame(LoginOrSignUp)

    def switch_frame(self, frame_class):
        """
        destroys current frame and switches to a new frame
        :param frame_class: a ctkFrame class
        :return: none
        """
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame

    def on_closing(self):
        """
        handles prtocol when closing the ctk window
        :return: none
        """
        global exit_all
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            for child in self.winfo_children():
                child.destroy()
            self.destroy()
            self.cli_s.close()
            exit_all = True


class MainApp(ctk.CTkFrame):
    def __init__(self, master):
        """
        initates the main screen of the platform
        :param master: a ctk.CTk master class
        """
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.cli_s = master.cli_s
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        self.udp_srv = threading.Thread(target=udp_server)
        self.udp_srv.start()
        time.sleep(0.3)
        self.recv_thread = threading.Thread(target=self.recv_thread_func)
        self.recv_thread.start()
        time.sleep(0.3)
        self.search_entry = None
        self.search_results = None
        self.files_frame = None
        self.search_progress = ctk.CTkProgressBar(self)
        self.search_label = ctk.CTkLabel(self, text=f'')

        self.share_files()
        title_label = ctk.CTkLabel(self, text='Welcome to Agamusic!', font=(FONT, 24))
        title_label.pack(pady=10)
        self.search_entry = ctk.CTkEntry(self, font=(FONT, 14))
        self.search_entry.pack(pady=5)

        search_button = ctk.CTkButton(self, text='Search', command=self.search, font=(FONT, 14))
        search_button.pack(pady=10)

        my_dir_button = ctk.CTkButton(self, text='My Library', command=self.show_library, font=(FONT, 14))
        my_dir_button.pack(pady=10)

    def recv_thread_func(self):
        """
        handles the messages from the server
        :return: none
        """
        global exit_all
        while True:
            data = recv_by_size(self.cli_s)
            if exit_all:
                break
            if data == "":
                print("seems server DC")
                tk.messagebox.showerror('Error', 'Server Disconnected')
                exit_all = True
                break
            if len(data) < 6:
                print("seems bad message format:" + data)
                break
            self.data_recv(data)
        return

    def data_recv(self, data):
        """
        gets the data from server and generates the response (to screen)
        :param data: data received from server
        :return: none
        """
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
            self.search_progress.stop()
            self.search_progress.destroy()
            if self.search_label is not None:
                self.search_label.configure(text='')
                self.search_label.pack()
            self.search_results = SearchResult(self, fields, self.cli_s)

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
            md5 = fields[7]
            time.sleep(0.5)
            udp_cli = threading.Thread(target=udp_client,
                                       args=(CLI_PATH, fip, fname, fsize, ftoken, song_name, artist, genre, md5))
            udp_cli.start()
            print("Run udp client to download the file " + fname + " from " + fip)
            udp_cli.join()
            if md5 in local_files.keys():
                tk.messagebox.showinfo('Download Status', f'{fname} downloaded succesfully from {fip}')
            else:
                tk.messagebox.showerror('Download Status', f"{fname} couldn't be downloaded. Please Try again later")

        elif action == "SENDTK":  # server sends to listening client
            token = fields[0]
            start_time = fields[1]
            token_lock.acquire()
            token_dict[token] = start_time
            print(token_dict)
            token_lock.release()
            print('added-- ', token, " --to dict")
            self.send_token_ack()

        elif action == "AMLIVE":
            print("Server answer and Live")

        elif action == "ERRORS":
            tk.messagebox.showerror(f"Error {fields[0]}", fields[1])

        else:
            print("Unknown action back " + action)

    def show_library(self):
        """
        calls ShowLibrary class when button is pressed
        :return: none
        """
        if self.files_frame is not None:
            self.files_frame.destroy()
        self.library = ShowLibrary(self)

    def search(self):
        """
        handles the search function when the user is searching for a song
        :return: none
        """
        keyword = self.search_entry.get()
        self.search_label.configure(text=f"searching for '{keyword}'...", font=(FONT, 12))
        self.search_label.pack()
        self.search_progress = ctk.CTkProgressBar(self)
        self.search_progress.set(0)
        self.search_progress.pack(pady=2)
        self.search_progress.start()
        to_send = "SEARCH|" + keyword + '|' + USERNAME
        send_with_size(self.cli_s, to_send)

    def get_file(self, md5):
        """
        handles the request to download song from client
        :param md5: the req file's md5
        :return: none
        """
        to_send = "LINKFN|" + md5
        send_with_size(self.cli_s, to_send)

    def share_files(self):
        """
        handles the upload of shared files information
        :return: none
        """
        to_send = "UPLOAD|" + str(len(local_files))
        for file, song in local_files.items():
            to_send += f"|{song.md5}~{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{USERNAME}~{song.size}"
        send_with_size(self.cli_s, to_send)

    def send_token_ack(self):
        """
        sends token acknowledgment to server when a token is recieved
        :return: none
        """
        to_send = "TOKACK"
        send_with_size(self.cli_s, to_send)


class ShowLibrary(ctk.CTkFrame):
    def __init__(self, master):
        """
        initates the library frame
        :param master: the master frame object
        """
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.8, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='My Library', font=(FONT, 18))
        title_label.pack(pady=10)

        self.toplevel_window = None

        # Create a table to display the song information
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['Song', 'Artist', 'Genre', 'Play']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=(FONT, 14), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')

        i = 0
        for song in local_files.values():
            song_label = ctk.CTkLabel(table_frame, text=song.song_name, font=(FONT, 14), padx=10, pady=5)
            song_label.grid(row=i + 1, column=0, sticky='w')

            artist_label = ctk.CTkLabel(table_frame, text=song.artist, font=(FONT, 14), padx=10, pady=5)
            artist_label.grid(row=i + 1, column=1, sticky='w')

            genre_label = ctk.CTkLabel(table_frame, text=song.genre, font=(FONT, 14), padx=10, pady=5)
            genre_label.grid(row=i + 1, column=2, sticky='w')

            play_button = ctk.CTkButton(table_frame, command=lambda fullname=os.path.join(CLI_PATH, song.file_name),
                                                                    song_name=song.song_name:
            self.open_toplevel(fullname, song_name), text=f'Play')
            play_button.grid(row=i + 1, column=3, sticky='w')
            i += 1

    def open_toplevel(self, fullname, song_name):
        """
        opens a song play window when user presses the play button
        :param fullname: the file's full path
        :param song_name: the song's name
        :return: none
        """
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = SongWindow(self, fullname, song_name)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it


class SongWindow(ctk.CTkToplevel):
    def __init__(self, master, file, song_name, *args, **kwargs):
        """
        initates the song's play window
        :param master: the master frame object
        :param file: file's path
        :param song_name: the song's name
        """
        super().__init__(*args, **kwargs)
        self.master = master
        self.file = file
        self.song_name = song_name
        self.geometry("400x300")
        self.title(f"{song_name}")

        self.label = ctk.CTkLabel(self, text=f"Playing {self.song_name}", font=(FONT, 14))
        self.label.pack(padx=20, pady=20)
        self.current_lbl = ctk.CTkLabel(self, text="00:00/00:00", font=(FONT, 14))
        self.current_lbl.pack()
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=2)
        pause_image = ctk.CTkImage(Image.open('pause_button_bg.png'), size=(75, 90))
        self.pause_btn = ctk.CTkButton(table_frame, command=self.pause, font=(FONT, 14), image=pause_image, text='')
        self.pause_btn.grid(row=0, column=0, sticky='w')
        play_image = ctk.CTkImage(Image.open('play_button_bg.png'), size=(75, 90))
        self.play_btn = ctk.CTkButton(table_frame, command=self.play, font=(FONT, 14), image=play_image, text='')
        self.play_btn.grid(row=0, column=1, sticky='w')

        self.play_bar = ctk.CTkProgressBar(self)
        self.play_bar.set(0)
        self.play_bar.pack(pady=2)
        self.paused = True
        self.playing = False

        self.audio_length = 0
        self.current_sec = 0
        self.after_id = None
        self.audio_length = 0

    def start_playing(self):
        """
        Starts playing the audio file specified by `self.file`
        :return: none
        """
        p = pyaudio.PyAudio()
        chunk = 1024
        with wave.open(self.file, "rb") as wf:

            self.audio_length = wf.getnframes() / float(wf.getframerate())
            self.play_bar.configure(indeterminate_speed=1 / self.audio_length)
            stream = p.open(format=
                            p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True)

            data = wf.readframes(chunk)

            chunk_total = 0
            self.play_bar.start()
            while data != b"" and self.playing:

                if not self.paused:
                    chunk_total += chunk
                    stream.write(data)
                    data = wf.readframes(chunk)
                    self.current_sec = chunk_total / wf.getframerate()

        self.playing = False
        stream.close()
        p.terminate()

    def pause(self):
        """
        Pauses the audio playback
        :return: none
        """
        self.paused = True

        if self.after_id:
            self.current_lbl.after_cancel(self.after_id)
            self.after_id = None

        self.play_bar.stop()

    def play(self):
        """
        Plays the audio playback
        :return: none
        """
        if not self.playing:
            self.playing = True
            threading.Thread(target=self.start_playing, daemon=True).start()

        if self.after_id is None:
            self.update_lbl()

        self.paused = False
        self.play_bar.start()

    def stop(self):
        """
        stops the audio playback completely
        :return: none
        """
        self.playing = False
        if self.after_id:
            self.current_lbl.after_cancel(self.after_id)
        self.after_id = None

    def update_lbl(self):
        """
        Updates the current time label and progress bar during audio playback
        :return: none
        """
        self.current_lbl.configure(text=f"{int(self.current_sec // 60):02d}:{int(self.current_sec % 60):02d}/"
                                        f"{int(self.audio_length // 60):02d}:{int(self.audio_length % 60):02d}")

        self.after_id = self.current_lbl.after(5, self.update_lbl)
        if self.audio_length != 0:
            current_progress = self.current_sec / self.audio_length
            self.play_bar.set(current_progress)


class LocalFiles(ctk.CTkFrame):
    def __init__(self, master):
        """
        initates the local file loading screen that gets input from the user about their shared files
        :param master: the master ctk.CTk class
        """
        print('got to local files')
        self.files_list = [f for f in os.listdir(CLI_PATH) if
                           os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.wav')]
        print(self.files_list)
        if len(self.files_list) == 0:
            print('len is 0')
            master.switch_frame(MainApp)
            print('switched to main')
            return
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)

        title_label = ctk.CTkLabel(self, text='Add Local Files', font=(FONT, 18))
        title_label.pack(pady=10)

        # Create a table to display the song information
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['File Name', 'Song Name', 'Artist', 'Genre']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=(FONT, 12), padx=10, pady=5)
            header_label.grid(row=0, column=i, sticky='w')

        # Get the local files in the directory
        self.files_list = [f for f in os.listdir(CLI_PATH) if
                           os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.wav')]
        print(self.files_list)
        # Add the rows to the table for each local file
        for i, file_name in enumerate(self.files_list):
            # Create the labels for the file name, song name, artist, and genre
            file_name_label = ctk.CTkLabel(table_frame, text=file_name, font=(FONT, 12), padx=10, pady=5)
            file_name_label.grid(row=i + 1, column=0, sticky='w')

            song_name_entry = ctk.CTkEntry(table_frame, font=(FONT, 12))
            song_name_entry.grid(row=i + 1, column=1, sticky='w')

            artist_entry = ctk.CTkEntry(table_frame, font=(FONT, 12))
            artist_entry.grid(row=i + 1, column=2, sticky='w')

            genre_entry = ctk.CTkEntry(table_frame, font=(FONT, 12))
            genre_entry.grid(row=i + 1, column=3, sticky='w')

            # Save the information when the user clicks the save button
            save_button = ctk.CTkButton(table_frame, text='Save', font=(FONT, 12),
                                        command=lambda f=file_name, sn=song_name_entry, a=artist_entry,
                                                       g=genre_entry: self.save_song_info(f, sn.get(), a.get(),
                                                                                          g.get()))
            save_button.grid(row=i + 1, column=4, padx=10)

        continue_button = ctk.CTkButton(self, text='Continue', font=(FONT, 12), command=self.continue_to_main)
        continue_button.place(relx=0.4, rely=0.7)

    def save_song_info(self, file_name, song_name, artist, genre):
        """
        saves the inputted song's information to local_files
        :param file_name: the file's name
        :param song_name: the song's name
        :param artist: the artist
        :param genre: the genre of the song
        :return:  none
        """
        global local_files, SAVED_FILES
        md5 = hashlib.md5(open(os.path.join(CLI_PATH, file_name), 'rb').read()).hexdigest()
        if md5 not in local_files.keys() and song_name != '' and artist != '' and genre != '':
            if "'" in song_name or "'" in artist or "'" in genre:
                tk.messagebox.showwarning('Warning',
                                          "The song information contains non valid chars and cannot be saved")
                return
            local_files[md5] = Song(md5, file_name, song_name, artist, genre, USERNAME,
                                    size=os.path.getsize(os.path.join(CLI_PATH, file_name)))
            saved_label = ctk.CTkLabel(self, text=f"{file_name} saved", font=(FONT, 12), padx=10, pady=5)
            saved_label.pack(pady=10)
        else:
            not_saved_label = ctk.CTkLabel(self, text=f"{file_name} already saved", font=(FONT, 12), padx=10, pady=5)
            not_saved_label.pack(pady=10)

    def continue_to_main(self):
        """
        when continue button is pressed,
        this function checks that all information was saved and switches over to main frame
        :return: none
        """
        if len(local_files) == len(self.files_list):
            self.master.switch_frame(MainApp)
        else:
            tk.messagebox.showerror('Error', 'Please fill out all spaces before continue')


class SearchResult(ctk.CTkScrollableFrame):
    def __init__(self, master, fields, cli_s):
        """
        initsaes the search result frame class. Displays the results received from the server
        :param master: a frame class object
        :param fields: the fields from the server's message
        :param cli_s: the client's socket
        """
        self.master = master
        self.cli_s = cli_s
        ctk.CTkScrollableFrame.__init__(self, master)
        self.update_idletasks()
        self.place(anchor='center', relx=0.5, rely=0.8, relheight=0.95, relwidth=0.95)
        self.configure()
        title_label = ctk.CTkLabel(self, text='Search Results', font=(FONT, 18))
        title_label.pack(pady=10)

        # Create a table to display the search results
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        if fields[0] == '':
            empty_label = ctk.CTkLabel(self, text=f"No search results", font=(FONT, 16))
            empty_label.pack(pady=10)

        else:
            headers = ['File Name', 'Song', 'Artist', 'Genre', 'Size', 'Username', 'Download']
            for i, header in enumerate(headers):
                header_label = ctk.CTkLabel(table_frame, text=header, font=(FONT, 14), padx=10, pady=5)
                header_label.grid(row=0, column=i, sticky='w')

            # Add the search results to the table
            i = 1
            for f in fields:
                info = f.split("~")
                md5 = info[0]
                print(info)
                file_name = ctk.CTkLabel(table_frame, text=info[1], font=(FONT, 14), padx=10, pady=2, wraplength=150)
                file_name.grid(row=i + 1, column=0, sticky='w', pady=10)

                song_label = ctk.CTkLabel(table_frame, text=info[2], font=(FONT, 14), padx=10, pady=2, wraplength=150)
                song_label.grid(row=i + 1, column=1, sticky='w', pady=10)

                artist_label = ctk.CTkLabel(table_frame, text=info[3], font=(FONT, 14), padx=10, pady=2, wraplength=150)
                artist_label.grid(row=i + 1, column=2, sticky='w', pady=10)

                genre_label = ctk.CTkLabel(table_frame, text=info[4], font=(FONT, 14), padx=10, pady=2, wraplength=150)
                genre_label.grid(row=i + 1, column=3, sticky='w', pady=10)

                size_label = ctk.CTkLabel(table_frame, text=info[5], font=(FONT, 14), padx=10, pady=2, wraplength=150)
                size_label.grid(row=i + 1, column=4, sticky='w', pady=10)

                username_label = ctk.CTkLabel(table_frame, text=info[6], font=(FONT, 14), padx=10, pady=2,
                                              wraplength=150)
                username_label.grid(row=i + 1, column=5, sticky='w', pady=10)
                print(info[7])
                if info[7] == 'True':
                    print('got to available')
                    download_button = ctk.CTkButton(table_frame, command=lambda f=md5: self.get_file(f),
                                                    text='Download!', font=(FONT, 14))
                else:
                    download_button = ctk.CTkButton(table_frame, text='Unavailable', font=(FONT, 14))

                download_button.grid(row=i + 1, column=6, sticky='w', pady=10)

                i += 1

    def get_file(self, md5):
        """
        requests a file from server if the download is available
        :param md5: the file's md5
        :return: none
        """
        to_send = "LINKFN|" + md5
        send_with_size(self.cli_s, to_send)


class LoginOrSignUp(ctk.CTkFrame):
    def __init__(self, master):
        """
        initiates the first displayed screen. Offers the option to login or signup
        :param master: a master ctk.CTk object
        """
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)

        self.cli_s = self.master.cli_s
        title_label = ctk.CTkLabel(self, text='Welcome!', font=(FONT, 24))
        title_label.pack(pady=10)

        login_button = ctk.CTkButton(self, text='Login', font=(FONT, 20),
                                     command=lambda: self.master.switch_frame(Login))
        login_button.pack(pady=10)

        signup_button = ctk.CTkButton(self, text='Sign up', font=(FONT, 20),
                                      command=lambda: self.master.switch_frame(Signup))
        signup_button.pack(pady=10)

        image = ctk.CTkImage(Image.open('logo.png'), size=(500, 312))
        image_label = ctk.CTkLabel(self, text='', image=image)
        image_label.pack(pady=15)


class Signup(ctk.CTkFrame):
    def __init__(self, master):
        """
        initaes the singup screen. handles with the username and password inputter from user
        :param master: a master ctk.CTk pbject
        """
        print('got to signup frame')
        ctk.CTkFrame.__init__(self, master)
        self.signed = False
        self.username = ''
        self.cli_s = master.cli_s

        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Sign Up', font=(FONT, 18))
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=(FONT, 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=(FONT, 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=(FONT, 12))
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=(FONT, 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='signup', font=(FONT, 12), command=self.signup_user)
        login_button.pack(pady=10)

    def valid_pass(self, password):
        """
        checks if the password is valid and follows the guidelines
        :param password: input password
        :return: valid/invalid
        """
        if len(password) < 8:
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        if not any(char.isdigit() for char in password):
            return False
        if any(char in "~-.:% " for char in password):
            return False
        return True

    def signup_user(self):
        """
        handles the communication with the server when signing up
        :return: none
        """
        global USERNAME, LOGGED
        while not self.signed:
            self.username = self.username_entry.get()
            password = self.password_entry.get()
            """if not self.valid_pass(password):
                tk.messagebox.showerror('Error',
                                        'The Password you have submitted is invalid. Password must follow these guidelines:'
                                        '\n• Must contain at least 8 chars'
                                        '\n• Must contain 1 uppercase letter, 1 lower case letter and 1 digit'
                                        '\n• Password cannot contain the following chars: ~-.:%')
                return"""
            to_send = f'SIGNUP|{self.username}|{password}'
            send_with_size(self.cli_s, to_send)
            result = recv_by_size(self.cli_s)
            if result[-2:] == 'OK':
                self.signed = True
                LOGGED = True
                USERNAME = self.username
            elif result[-2:] == 'NO':
                tk.messagebox.showerror('Error',
                                        'Username already exists or is currently logged, please try a different user')
        if self.signed:
            logging_label = ctk.CTkLabel(self, text='logging in...', font=(FONT, 12))
            logging_label.pack(pady=5)
            self.master.switch_frame(LocalFiles)


class Login(ctk.CTkFrame):
    def __init__(self, master):
        """
        initiates the login screen. handles with the username and password inputted from user
        :param master: a master ctk.CTk object
        """
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        self.logged = False
        self.username = ''
        self.cli_s = master.cli_s

        title_label = ctk.CTkLabel(self, text='Login', font=(FONT, 18))
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=(FONT, 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=(FONT, 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=(FONT, 12))
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=(FONT, 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='Login', font=(FONT, 12), command=self.login_user)
        login_button.pack(pady=10)

    def valid_pass(self, password):
        """
        checks if the password is valid and follows the guidelines
        :param password: input password
        :return: valid/invalid
        """
        if len(password) < 8:
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        if not any(char.isdigit() for char in password):
            return False
        if any(char in "~-.:%" for char in password):
            return False
        return True

    def login_user(self):
        """
        handles the communication with the server when logging in
        :return: none
        """
        global LOGGED, USERNAME
        while not self.logged:
            try:
                self.username = self.username_entry.get()
                password = self.password_entry.get()
                """if not self.valid_pass(password):
                    tk.messagebox.showerror('Error',
                                            'The Password you have submitted is invalid. Password must follow these guidelines:'
                                            '\n• Must contain at least 8 chars'
                                            '\n• Must contain 1 uppercase letter, 1 lower case letter and 1 digit'
                                            '\n• Password cannot contain the following chars: ~-.:%')
                    return"""
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
                    tk.messagebox.showerror('Error', 'Exceeded maximum tries. Please try to log in later')
                    self.destroy()
                    break
                else:
                    tk.messagebox.showerror('Error', 'invalid username or password!')
                    return
            except Exception as e:
                print(e)
        if not self.logged:
            self.username = ''
        else:
            logging_label = ctk.CTkLabel(self, text='logging in...', font=(FONT, 12))
            logging_label.pack(pady=5)
            self.master.switch_frame(LocalFiles)


def udp_log(side, message):
    """
    logs udp communication into a .txt file
    :param side: which side is communicating to the log (server or client)
    :param message: the logged message
    :return: none
    """
    with open("udp_" + side + "_log.txt", 'a') as log:
        log.write(str(datetime.datetime.now())[:19] + " - " + message + "\n")
        if LOG_ALL:
            print(message)


def check_valid_token(token):
    """
    checks if the given token is in the dictionary
    :param token: the token from the client requesting a file
    :return: valid or invalid token
    """
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


def udp_server():
    """
    gets file request and will send Binary file data
    :param cli_path: the client's path to local shared folder
    :return: none
    """
    """
    will get file request and will send Binary file data
    """
    global local_files
    cli_path=CLI_PATH
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
                md5 = fields[0]
                fsize = int(fields[1])
                ftoken = fields[2]
                print(md5, fsize, ftoken)
                if check_valid_token(ftoken):
                    if md5 in local_files.keys():
                        if local_files[md5].size == fsize and fsize > 0:
                            fullname = os.path.join(cli_path, local_files[md5].file_name)
                            udp_file_send(udp_sock, fullname, fsize, addr)
                            time.sleep(5)
                        else:
                            udp_log("server", "sizes not ok")
                    else:
                        udp_log("server", "file not found " + md5)
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
    """
    Sends a file over UDP to the specified address.
    :param udp_sock: The UDP socket used for sending the file.
    :param fullname: The full path of the file to be sent.
    :param fsize: The size of the file in bytes.
    :param addr: The address (IP and port) of the destination.
    :return: None
    """
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


def udp_client(cli_path, ip, fn, size, token, song_name, artist, genre, md5):
    """
    Sends a request to the UDP server and receives a file if the request is successful.
    :param cli_path: The path to the client directory where the file will be saved.
    :param ip: The IP address of the UDP server.
    :param fn: The filename of the file to be requested.
    :param size: The size of the file in bytes.
    :param token: The token for authentication.
    :param song_name: The name of the song.
    :param artist: The artist of the song.
    :param genre: The genre of the song.
    :param md5: The MD5 hash of the file.
    :return: None
    """
    global local_files
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addr = (ip, UDP_PORT)
    udp_sock.settimeout(10)
    send_ok = False

    to_send = "FRQ|" + md5 + "|" + str(size) + "|" + token
    try:
        udp_sock.sendto(to_send.encode(), addr)
        send_ok = True
        if DEBUG:
            udp_log("client", "Sent " + to_send + " to " + addr[0] + " " + str(addr[1]))

    except socket.timeout:
        print("timeout on socket - No answer")
    except socket.error as e:
        if e.errno == 10040:
            udp_log("client", "Send failed Too large file")
        else:
            udp_log("client", "Send failed general socket error  " + e.message)

    if send_ok and size > 0:
        saved = udp_file_recv(udp_sock, os.path.join(cli_path, fn), size)

        if saved:
            check_md5 = hashlib.md5(open(fn, 'rb').read()).hexdigest()
            if check_md5 == md5:
                local_files[md5] = Song(fn, song_name, artist, genre, USERNAME, md5, size=size)
            else:
                print('md5 of file is wrong', check_md5, md5)

    else:
        if DEBUG:
            udp_log('client', "Send failed or size = 0")
    udp_sock.close()

def udp_file_recv(udp_sock, fullname, size):
    """
    Receives a file over UDP and saves it to the specified location.
    :param udp_sock: The UDP socket used for receiving data.
    :param fullname: The full path of the file to be saved.
    :param size: The size of the file in bytes.
    :return: True if the file is successfully received and saved, False otherwise.
    """
    done = False
    file_pos = 0
    received_packets = {}
    expected_packet = 1

    try:
        f_write = open(fullname, 'wb')

        while not done:
            data, addr = udp_sock.recvfrom(FILE_PACK_SIZE + HEADER_SIZE)
            if data == b"":
                return False

            header = data[:HEADER_SIZE].decode()
            pack_size = int(header[:9])
            pack_cnt = int(header[10:18])
            pack_checksum = header[19:]
            bin_data = data[HEADER_SIZE:]

            m = hashlib.md5()
            m.update(bin_data)
            checksum = m.hexdigest()

            if checksum != pack_checksum:
                udp_log("client", "Checksum error pack " + str(pack_cnt))
                continue

            if pack_cnt == expected_packet:
                f_write.write(bin_data)
                file_pos += pack_size
                expected_packet += 1

                if file_pos >= size:
                    done = True

                # Write any buffered packets that arrived out of order
                while expected_packet in received_packets:
                    f_write.write(received_packets[expected_packet])
                    file_pos += len(received_packets[expected_packet])
                    expected_packet += 1
                    del received_packets[expected_packet]

            else:
                # Buffer out-of-order packets
                received_packets[pack_cnt] = bin_data

    except socket.error as e:
        udp_log("client", "Failed to receive: " + str(e.errno) + str(e))
        return False

    f_write.close()

    if file_pos == size:
        udp_log("client", "UDP Download Done " + fullname + " len=" + str(size))
        return True
    else:
        udp_log("client", "Something went wrong. Can't download " + fullname)
        return False


def move_old_to_file(f_data, last, max, keep):
    """
    Moves the old data packets to the file.
    :param f_data: The file object for writing the data.
    :param last: The last packet number that was written to the file.
    :param max: The maximum packet number received.
    :param keep: The dictionary containing the data packets to be written.
    :return: The updated last packet number.
    """
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


def on_closing(app):
    """
    Closes the application window and handles the quit confirmation.
    :param app: The application object.
    :return: None
    """
    # Destroy all child frames
    for child in app.winfo_children():
        child.destroy()
    if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
        app.destroy()
        app.quit()


def main(cli_path, server_ip):
    """
    Starts the main application.
    :param cli_path: The path to the client directory.
    :param server_ip: The IP address of the server.
    :return: None
    """
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
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    try:
        app.mainloop()
    except tk.TclError as e:
        if "can't invoke" in str(e):
            pass  # ignore the error since the root window has already been destroyed

    print('goodbye')
    exit()


if __name__ == "__main__":
    if len(argv) > 2:
        sys.path.append(r"E:\finalProject\venv\Lib\site-packages\customtkinter")
        main(argv[1], argv[2])

    else:
        print("USAGE : <enter client folder> <server_ip>")
        exit()
