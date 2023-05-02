
"""import pytube as pt
import audiosegment
import os
import glob
from pydub import AudioSegment"""

"""
url = input("please enter youtube link:")

yt = pt.YouTube(url)
print("downloading song")
t = yt.streams.filter(only_audio=True)
print(t[0])
t[0].download(filename='testing.mp4')
"""

# AudioSegment.from_file('Adele - Hello (Official Music Video).mp4')
"""
import datetime
#import ctk
import customtkinter as ctk
print(str(datetime.datetime.now()))

class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.CTk.__init__(self)
"""
"""
class hello():
    def __init__(self):
        print(get_name())

def get_name():
    return 'agam'

h = hello()"""
"""import sqlCommands
songs_database = sqlCommands.SongsORM('server_database.db')
users_database = sqlCommands.UserORM('server_database.db')
songs = songs_database.search_songs('rock')
answer = 'SCH_BACK'
if len(songs) == 0:
    answer += ''
else:
    for song in songs:
        is_available = users_database.is_available(song.file_name)
        print(is_available)
        username = songs_database.get_user_by_song(song.file_name)
        print(username)
        answer += f"|{song.song_name}~{song.artist}~{song.genre}~{song.size}~{username}~{is_available}"

""""""
from sqlCommands import Song
local_files= {Song('fn','sn','a','rock','agam8'), Song('hello.mp3','hello','adele','r&b','Agam8')}
for i, song in enumerate(local_files):
    print(i, song.file_name, song.song_name,song.artist,song.genre,song.committed_user)"""
