import json
import os
import time
from os import path

import requests
from utils import Config
from natsort import os_sorted
# from requests_toolbelt.multipart.encoder import MultipartEncoder

# This deals with overwriting of existing lessons / collections.
# The main usecase is to add audio to an already uploaded book where some
# editing has already be done, and we wouldn't want to upload the text again.

# The blank audios were found here: https://github.com/anars/blank-audio

# Change these two. Pk is the id of the collection
# pk = "1070313" # Quick imports
LANGUAGE_CODE = "ja"
COURSE_ID = "537808"


def E(myjson):
    json.dump(myjson, ensure_ascii=False, indent=2)


# TODO: implement the changes from the updated "post.py" script
def read(folder):
    """Returns a human sorted list of non-hidden directories"""
    return [
        f
        for f in os_sorted(os.listdir(folder))
        if path.isfile(path.join(folder, f)) and not f.startswith(".")
    ]


def double_check():
    if input("Proceed? [y/n] ") != "y":
        print("Exiting")
        exit(1)


# collection is a json-like dict
def iter_lessons_from_collection(config: Config, collection, fr_lesson: int, to_lesson: int):
    for lesson in collection["lessons"][fr_lesson - 1 : to_lesson]:
        response = requests.get(lesson["url"], headers=config.headers)

        if response.status_code != 200:
            print(f"Error in iter_lesson for lesson: {lesson['title']}")
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")
            break

        lesson_json = response.json()
        yield lesson_json


def patch_blank_audio(config: Config, collection, from_lesson, to_lesson, sleep=0):
    print(f"Patching blank audio for course: {COURSE_ID}, in language: {LANGUAGE_CODE}")
    double_check()

    lesson_iter = iter_lessons_from_collection(config, collection, from_lesson, to_lesson)
    lessons = list(lesson_iter)
    max_iterations = len(lessons)
    blank_audio_path = "15-seconds-of-silence.mp3"

    for idx, lesson in enumerate(lessons, 1):
        patch_audio(config, blank_audio_path, lesson, idx, max_iterations, sleep)

    print("patch_blank_audio finished!")


def patch_bulk_audios(config: Config, collection, audios, from_lesson, to_lesson, sleep=0):
    lesson_iter = iter_lessons_from_collection(config, collection, from_lesson, to_lesson)
    lessons = list(lesson_iter)
    max_iterations = len(lessons)

    # Confirm the patching
    for idx, (audio_path, lesson) in enumerate(zip(audios, lessons), 1):
        print(f"{audio_path} -> {lesson['title']}")
    double_check()

    for idx, (audio_path, lesson) in enumerate(zip(audios, lessons), 1):
        audio_path = path.join("audios", audio_path)
        patch_audio(config, audio_path, lesson, idx, max_iterations, sleep)

    print("patch_bulk_audios finished!")


def patch_audio(config: Config, audio_path, lesson, idx, max_iterations, sleep):
    url = f"{Config.API_URL_V3}{LANGUAGE_CODE}/lessons/{lesson['id']}/"
    files = {"audio": open(audio_path, "rb")}
    response = requests.patch(url=url, headers=config.headers, files=files)

    if response.status_code != 200:
        print(f"Error in patch blank audio for lesson: {lesson['title']}")
        print(f"Response code: {response.status_code}")
        print(f"Response text: {response.text}")
        return

    print(f"[{idx}/{max_iterations}] Patched audio for: {lesson['title']}")

    time.sleep(sleep)


def resplit_japanese(config: Config, collection, from_lesson, to_lesson, sleep=0):
    """Re-split an existing lesson in japanese with ichimoe"""

    assert LANGUAGE_CODE == "ja"
    print(f"Resplitting audio for course: {COURSE_ID}, in language: {LANGUAGE_CODE}")
    double_check()

    for lesson in iter_lessons_from_collection(config, collection, from_lesson, to_lesson):
        lesson_id = lesson["id"]

        url = f"{Config.API_URL_V3}{LANGUAGE_CODE}/lessons/{lesson_id}/resplit/"
        data = {"method": "ichimoe"}

        response = requests.post(url=url, headers=config.headers, data=data)

        if response.status_code != 200:
            print(f"Error in patch blank audio for lesson: {lesson['title']}")
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")
            return

        print(f"Resplit text for: {lesson['title']}")

        time.sleep(sleep)


def main():
    config = Config()

    audios_folder = "audios"
    audios = read(audios_folder)

    url = f"{Config.API_URL_V2}{LANGUAGE_CODE}/collections/{COURSE_ID}"
    response = requests.get(url=url, headers=config.headers)
    collection = response.json()

    patch_blank_audio(config, collection, 1, 3)
    # patch_bulk_audios(config, collection, audios, 1, 2)
    # resplit_japanese(config, collection, 1, 2)


if __name__ == "__main__":
    main()
