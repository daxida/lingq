import sys, time
import os
from os import path
import copy
import json
from natsort import os_sorted
import requests
#from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import dotenv_values

# Change these two. Pk is the id of the collection
# pk = "1070313" # Quick imports
language_code = 'el'
pk = '1289772'

# Assumes that .env is on the root
PATH = os.getcwd()
parent_dir = os.path.dirname(PATH)
env_path = os.path.join(parent_dir, '.env')
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {'Authorization': f"Token {KEY}"}

# V3 or V2 doesn't change for this script
API_URL_V2 = 'https://www.lingq.com/api/v2/'


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def read(folder):
    '''Returns a human sorted list of non-hidden directories'''
    return [f for f in os_sorted(os.listdir(folder)) if path.isfile(path.join(folder, f)) and not f.startswith(".")]


def patchBlankAudio(collection, from_lesson, to_lesson, sleep=0):
    for lesson in collection['lessons'][from_lesson-1:to_lesson]:
        lesson = requests.get(
            lesson['url'], 
            headers=headers
        ).json()
        lesson_id = lesson["id"]

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/"
        
        audio = open(os.path.join("/Users/rafa/Desktop/lingq/", "15-seconds-of-silence.mp3"), 'rb')
        files = {'audio': audio}

        r = requests.patch(
            postAddress, 
            headers=headers, 
            files=files
        )

        if r.status_code == 400:
            print(r.text)
            exit()
        
        print(f"Patched audio for: {lesson['title']}")

        time.sleep(sleep)


def patchBulkAudios(collection, audios, from_lesson, to_lesson, sleep=0):
    for audio_path, lesson in list(zip(audios, collection['lessons']))[from_lesson-1:to_lesson]:
        lesson = requests.get(lesson['url'], headers=header).json()
        lesson_id = lesson["id"]

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/"
        
        audio = open(path.join("audios", audio_path), "rb")
        files = {'audio': audio}

        r = requests.patch(
            postAddress, 
            headers=headers, 
            files=files
        )

        if r.status_code == 400:
            print(r.text)
            exit()
        
        print(f"Patched audio for: {lesson['title']}")

        time.sleep(sleep)


def patchText(collection, from_lesson, to_lesson, sleep=0):
    for lesson in collection['lessons'][from_lesson-1:to_lesson]:
        lesson = requests.get(lesson['url'], headers=header).json()
        lesson_id = lesson["id"]

        text = open(os.path.join("/Users/rafa/Desktop/lingq/post/split", "Β'. Οι κατσίκες.txt"), 'r')

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/resplit/"
        
        m = MultipartEncoder([
                    ('text', text.read())]   
                )

        h = {'Authorization': 'Token ' + key,
            'Content-Type': m.content_type}

        r = requests.post(
            testAddress, 
            headers=h, 
            data=m
        )

        if r.status_code == 400:
            print(r.text)
            exit()
        
        print(f"Patched text for: {lesson['title']}")

        time.sleep(sleep)


def main():
    # audios_folder = "audios"
    # audios = read(audios_folder)

    collection = requests.get(
        f"{API_URL_V2}{language_code}/collections/{pk}", 
        headers=headers
    ).json()

    # patchBlankAudio(collection, 1, 1)
    # patchText(collection, 3, 3, 1)


if __name__ == '__main__':
    main()
    