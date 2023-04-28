
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

import datetime
#import ctk
import customtkinter as ctk
print(str(datetime.datetime.now()))

class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("light")
        ctk.CTk.__init__(self)
