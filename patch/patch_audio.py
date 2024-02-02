import sys, time
import os
from os import path
import json
from natsort import os_sorted
import requests


key = open(os.path.join("/Users/rafa/Desktop/lingq", "APIkey.txt")).read()
header = {"Authorization": "Token " + key}

language_code = "es"
pk = ""  # pk = "1070313" # Quick imports

API_URL_V2 = "https://www.lingq.com/api/v2/"
API_URL_V3 = "https://www.lingq.com/api/v3/"


def printJSON(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def read(folder):
    """Returns a human sorted list of non-hidden directories"""
    return [
        f
        for f in os_sorted(os.listdir(folder))
        if path.isfile(path.join(folder, f)) and not f.startswith(".")
    ]


def patchBlankAudio(collection, from_lesson, to_lesson, sleep=0):
    for lesson in collection["lessons"][from_lesson - 1 : to_lesson]:
        lesson = requests.get(lesson["url"], headers=header).json()
        lesson_id = lesson["id"]

        postAddress = f"{API_URL_V3}{language_code}/lessons/{lesson_id}/"

        audio = open(os.path.join("/Users/rafa/Desktop/lingq/", "15-seconds-of-silence.mp3"), "rb")
        files = {"audio": audio}

        r = requests.patch(postAddress, headers=header, files=files)

        if r.status_code == 400:
            print(r.text)
            exit()

        print(f"Patched audio for: {lesson['title']}")

        time.sleep(sleep)


def patchBulkAudios(collection, audios, from_lesson, to_lesson, sleep=0):
    for audio_path, lesson in list(zip(audios, collection["lessons"]))[from_lesson - 1 : to_lesson]:
        lesson = requests.get(lesson["url"], headers=header).json()
        lesson_id = lesson["id"]

        postAddress = f"{API_URL_V3}{language_code}/lessons/{lesson_id}/"

        audio = open(path.join("audios", audio_path), "rb")
        files = {"audio": audio}

        r = requests.patch(postAddress, headers=header, files=files)

        if r.status_code == 400:
            print(r.text)
            exit()

        print(f"Patched audio for: {lesson['title']}")

        time.sleep(sleep)


def main():
    audios_folder = "audios"
    audios = read(audios_folder)

    url = f"{API_URL_V2}{language_code}/collections/{pk}"
    collection = requests.get(url=url, headers=header).json()

    patchBulkAudios(collection, audios, 1, 100, 5)


if __name__ == "__main__":
    main()
