
"""import pytube as pt
import audiosegment
import os
import glob
from pydub import AudioSegment"""
import contextlib
import os.path

# import pytube.exceptions

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

"""
"""from sqlCommands import Song
local_files= {'filename1':Song('fn','sn','a','rock','agam8'), 'filename2':Song('hello.mp3','hello','adele','r&b','Agam8')}
i=0
for song in local_files.values():
    print(song)
    print(i, song.file_name, song.song_name,song.artist,song.genre,song.committed_user)
    i+=1"""
#from youtubesearchpython import VideosSearch

# import youtube_dl
# import pytube as pt
"""def download_pytube(video_url):
    try:
        yt = pt.YouTube(video_url)
        t = yt.streams.filter(only_audio=True)
        t[0].download()
    except pytube.exceptions.ExtractError as e:
        print(e)
def download_ytvid_as_mp3(video_url):
    print('downloading song')
    video_info = youtube_dl.YoutubeDL().extract_info(url = video_url,download=True)
    print(video_info)
    filename = f"{video_info['title']}.mp3"
    print(filename)
    options={
        'format':'bestaudio/best',
        'keepvideo':False,
        'outtmpl':filename,
    }
    with youtube_dl.YoutubeDL(options) as ydl:
        ydl.download([video_info['webpage_url']])
    print("Download complete... {}".format(filename))

videosSearch = VideosSearch('hello adele', limit = 1)
song_url = videosSearch.result()['result'][0]['link']
# download_ytvid_as_mp3(str(song_url))
download_pytube(song_url)
"""
"""from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from pydub import AudioSegment
import tempfile
import time"""



def download_wait(directory, timeout):
    """Wait for downloads to finish with a specified timeout."""
    seconds = 0
    dl_wait = True
    print('waiting for file to download')
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1
    time.sleep(5)


def download_youtube(url:str,directory:str):
  """youtube download"""
  url = "https://www.ss"+url[12:]

  option = Options()
  option.add_argument("--disable-extensions")
  option.add_argument("--start-maximized")
  option.add_experimental_option(
      "prefs", {"profile.default_content_setting_values.notifications": 2,"profile.default_content_settings.popups": 0,"download.default_directory" : directory}
  )

  driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=option)
  driver.get(url)
  driver.minimize_window()
  time.sleep(7)

  driver.find_element(By.CSS_SELECTOR,'[class="link link-download subname ga_track_events download-icon"]').click()

  time.sleep(2)

  try:
    w1 = driver.window_handles[0]
    w2 = driver.window_handles[1]
    driver.switch_to.window(window_name=w2)
    driver.close()
    driver.switch_to.window(w1)
    driver.minimize_window()
  except Exception as e:
      print(e)
  download_wait(directory,240)

def main(client_path):
    with contextlib.redirect_stdout as f:
        videosSearch = VideosSearch('hello adele', limit=1)
        url = videosSearch.result()['result'][0]['link']
        temp = tempfile.TemporaryDirectory()
        print()
        download_youtube(url, temp.name)
        fpath = f"{temp.name}\\{os.listdir(temp.name)[0]}"
        try:
            AudioSegment.from_file(fpath).export(f"{client_path}/{videosSearch.result()['result'][0]['title']}.wav",
                                                 format="wav")
        except Exception as e:
            print(e)
        time.sleep(5)
        try:
            os.remove(fpath)
            temp.cleanup()
        except Exception as e:
            print(e)


def action(**kwargs):
    song_name=kwargs['song_name']
    print(song_name)
import hashlib
def create_md5(filename):
    return hashlib.md5(open(filename,'rb').read()).hexdigest()

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
    last = 0
    max = 0
    keep = {}
    file_open = False
    all_ok = False
    checksum_error = False
    try:
        # Repeatedly receive data packets until the entire file is received
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
        udp_log("client", "Failed to receive: " + str(e.errno) + str(e))
        return False

    if all_ok:
        udp_log("client", "UDP Download Done " + fullname + " len=" + str(size))
        return True
    else:
        udp_log("client", "Something went wrong. Can't download " + fullname)
        return False
