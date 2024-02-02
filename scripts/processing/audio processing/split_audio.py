# https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04

# fmt: off

import os
from os import path
import sys
import subprocess

inputfile = sys.argv[1]
codec = '-acodec'

#ffmpeg did not like having '?' in the file name, add any other problematic symbol here.
escape_list = ['?']

def RemoveSymbols(text):
    for symbol in escape_list:
        text = text.replace(symbol, '')
    return text

tracklist = []

class Track:
    def __init__(self, timestamp, name):
        self.timestamp = timestamp
        self.name = name

class ExtractTracks:
    def __init__(self):
        with open(sys.argv[2], "r") as values:
            for value in values:
                name = ""
                timestamp = ""
                #split all by spaces.
                keyVal = value.split(' ')
                #find timestamp
                for word in keyVal:
                    if ':' in word:
                        timestamp = word
                    else:
                        name += word + ' '
                tracklist.append(Track(timestamp, name))

#Initialize
ExtractTracks()


def GenerateSplitCommand(start, end, filename):
    return ['ffmpeg', '-i', inputfile,  '-ss', start, '-to', end, '-c', 'copy', output_folder_name+"/"+filename+'.mp3', '-v', 'error']

def GetVideoEnd():
    ffprobeCommand = [
        'ffprobe',
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        '-sexagesimal',
        inputfile
    ]
    return subprocess.check_output(ffprobeCommand).strip()

def CreateOutputFolder(folder_name):
    if not path.exists(folder_name):
        os.mkdir(folder_name)

def ClearOutputFolder(folder_name):
    for file_name in os.listdir(folder_name):
        file = path.join(folder_name, file_name)
        if path.isfile(file):
            print('Deleting file:', file)
            os.remove(file)    


output_folder_name = "audios"
CreateOutputFolder(output_folder_name)
# ClearOutputFolder(output_folder_name)

for i in range(0, len(tracklist)):
    name = tracklist[i].name.strip()
    name = RemoveSymbols(name)
    startTime = tracklist[i].timestamp.strip()
    if i != (len(tracklist) - 1):
        endTime = tracklist[i+1].timestamp.strip() #- startTime
    else:
        endTime = GetVideoEnd() #- startTime
        endTime = endTime.decode('ascii')  # b'5:53:46.272000' -> 5:53:46.272000

    print(f'Generating {name} from {startTime} to {endTime}')

    command = GenerateSplitCommand(str(startTime), str(endTime), name)
    output = subprocess.check_call(command)
