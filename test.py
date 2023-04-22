
"""import pytube as pt
import audiosegment
import os
import glob
from pydub import AudioSegment"""
import sqlCommands

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
print(str(datetime.datetime.now()))

"""
"""
users_database = sqlCommands.UserORM('server_database.db')
verify = users_database.login('Agam8','12345678','127.0.0.1')
print(verify)
logout = users_database.logout('Agam8')
"""
print("LOG_BACK|OK"[-2:])