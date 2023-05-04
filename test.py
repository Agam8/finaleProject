
"""import pytube as pt
import audiosegment
import os
import glob
from pydub import AudioSegment"""
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
from youtubesearchpython import VideosSearch
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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from pydub import AudioSegment
import tempfile
import time



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
    time.sleep(10)


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
    videosSearch = VideosSearch('hello adele', limit=1)
    url = videosSearch.result()['result'][0]['link']
    temp = tempfile.TemporaryDirectory()
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


main('client_songs')