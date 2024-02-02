import time
import os
from natsort import os_sorted
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import dotenv_values
from typing import List

# post_text seems to work but it has been a long time since I tried post_text_and_audio.
# The same goes for patch_text, although now that the limit is 6k words it should be fine.

# The preprocessed split text.txt files should be in texts_folder
# and the same goes for the .mp3 in AUDIOS_FOLDER
# This assumes that they are paired in a way that zipping them makes sense.

# Change these:
TEXTS_FOLDER = "split"
# If you want to post only text, set AUDIOS_FOLDER to None
AUDIOS_FOLDER = None
# 1-idxed, 1 is the first lesson.
# Just write an arbitrarily high number in TO_LESSON to post everything.
FR_LESSON = 1
TO_LESSON = 99

# Time in seconds to wait between requests
SLEEP_SECONDS = 2

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

############################################################

# Assumes that .env is on the root and than this script is run inside post/ folder
PATH = os.getcwd()
parent_dir = os.path.dirname(PATH)
env_path = os.path.join(parent_dir, ".env")
KEY = dotenv_values(env_path)["APIKEY"]

LINGQ_API_URL_V3 = f"https://www.lingq.com/api/v3/{LANGUAGE_CODE}/"
IMPORT_URL = f"{LINGQ_API_URL_V3}lessons/import/"


def get_greek_sorting_fn():
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Ι'. Η μάχη -> 10
    NUMERALS = "Α Β Γ Δ Ε ΣΤ Ζ Η Θ Ι ΙΑ ΙΒ ΙΓ ΙΔ ΙΕ ΙΣΤ ΙΖ".split()
    ORDER = [f"{num}'" for num in NUMERALS]

    def sorting_fn(x):
        return ORDER.index(x.split(".")[0])

    return sorting_fn


def get_roman_sorting_fn():
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Chapitre X.mp3 -> X
    import roman

    def sorting_fn(x):
        return roman.fromRoman((x.split()[1]).split(".")[0])

    return sorting_fn


def read_sorted_folders(folder: str, mode: str) -> List:
    if mode == "human":
        sorting_fn = os_sorted
    elif mode == "greek":
        sorting_fn = get_greek_sorting_fn()
    elif mode == "roman":
        sorting_fn = get_roman_sorting_fn()
    else:
        print("Unsupported mode in read_folder")
        exit(1)

    return [
        f
        for f in sorting_fn(os.listdir(folder))
        if os.path.isfile(os.path.join(folder, f)) and not f.startswith(".")
    ]


def post_text():
    texts = read_sorted_folders(TEXTS_FOLDER, mode="human")

    for text_filename in texts[FR_LESSON - 1 : TO_LESSON]:
        title = text_filename.replace(".txt", "")

        file_path = os.path.join(TEXTS_FOLDER, text_filename)
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        m = MultipartEncoder(
            [
                ("title", title),
                ("text", text),
                ("collection", COURSE_ID),
                ("save", "true"),
            ]
        )

        headers = {"Authorization": f"Token {KEY}", "Content-Type": m.content_type}

        response = requests.post(url=IMPORT_URL, data=m, headers=headers)

        if response.status_code != 201:
            print("Error:")
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")
            return

        print(f"  Posted text for lesson {title}")

        time.sleep(SLEEP_SECONDS)


def post_text_and_audio():
    texts = read_sorted_folders(TEXTS_FOLDER, mode="human")
    audios = read_sorted_folders(AUDIOS_FOLDER, mode="human")
    pairs = list(zip(texts, audios))

    for text_filename, audio_filename in pairs[FR_LESSON - 1 : TO_LESSON]:
        title = text_filename.replace(".txt", "")
        text = open(os.path.join(TEXTS_FOLDER, text_filename), "r").read()
        audio = open(os.path.join(AUDIOS_FOLDER, audio_filename), "rb")

        m = MultipartEncoder(
            [
                ("title", title),
                ("text", text),
                ("collection", COURSE_ID),
                ("audio", (audio_filename, audio, "audio/mpeg")),
                ("save", "true"),
            ]
        )

        headers = {"Authorization": f"Token {KEY}", "Content-Type": m.content_type}

        response = requests.post(IMPORT_URL, data=m, headers=headers)

        if response.status_code != 201:
            print("Error:")
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")
            return

        print(f"Title: {title}")
        print(f"Audio: {audio_filename}")
        print(f"Posted text and audio for lesson {title}")

        time.sleep(SLEEP_SECONDS)


def patch_text(collection, texts_folder, from_lesson, to_lesson, sleep):
    """
    OUTDATED - plus now LingQ allows for +2k words limit

    Patches them with text over the 2k words limit
    """

    print("Patching text!")

    texts = read_sorted_folders(texts_folder, mode="human")
    pairs = list(zip(texts, collection["lessons"]))

    for text_filename, lesson in pairs[from_lesson - 1 : to_lesson]:
        lesson = requests.get(lesson["url"], headers=header).json()  # header?
        lesson_id = lesson["id"]

        text = open(os.path.join(texts_folder, text_filename), "r").read()

        postAddress = f"{LINGQ_API_URL_V3}lessons/{lesson_id}/resplit/"

        m = MultipartEncoder([("text", text)])

        h = {"Authorization": "Token " + KEY, "Content-Type": m.content_type}

        r = requests.post(postAddress, headers=h, data=m)

        if r.status_code == 400:
            print(r.text)
            exit()

        print(f"Patched text for: {lesson['title']}")

        time.sleep(sleep)


def main():
    if not TEXTS_FOLDER:
        print("No texts folder declared, exiting!")
        return 

    url = f"https://www.lingq.com/en/learn/{LANGUAGE_CODE}/web/editor/courses/{COURSE_ID}"
    print(f"Starting upload at {url}")

    if AUDIOS_FOLDER:
        print(f"Posting text and audio for lessons {FR_LESSON} to {TO_LESSON}...")
        post_text_and_audio()
    else:
        print(f"Posting text for lessons {FR_LESSON} to {TO_LESSON}...")
        post_text()


if __name__ == "__main__":
    main()
