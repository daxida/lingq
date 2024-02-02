import sys, time
import os
from os import path
import json
from natsort import os_sorted
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# TODO: implement the changes from the updated "post.py" script


key = open(os.path.join("/Users/rafa/Desktop/lingq", "APIkey.txt")).read()
header = {"Authorization": "Token " + key, "Content-Type": "application/json; charset=UTF-8"}
API_URL_V2 = "https://www.lingq.com/api/v2/"

language_code = "el"
pk = "1137696"  # pk = "1070313" # Quick imports


def printJSON(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def readGreekNumerals(folder):
    # fmt: off
    order = ["Α'", "Β'", "Γ'", "Δ'", "Ε'", "ΣΤ'", "Ζ'", "Η'", "Θ'", "Ι'", "ΙΑ'", "ΙΒ'", "ΙΓ'", "ΙΔ'", "ΙΕ'", "ΙΣΤ'", "ΙΖ'"]
    # fmt: on
    files = [
        f for f in os.listdir(folder) if path.isfile(path.join(folder, f)) and not f.startswith(".")
    ]
    # Ι'. Η μάχη -> 10
    return sorted(files, key=lambda x: order.index(x.split(".")[0]))


def read(folder):
    """Returns a human sorted list of non-hidden directories"""
    return [
        f
        for f in os_sorted(os.listdir(folder))
        if path.isfile(path.join(folder, f)) and not f.startswith(".")
    ]


def patchBulkAudios(collection, audios, from_lesson, to_lesson, sleep=0):
    for audio_path, lesson in list(zip(audios, collection["lessons"]))[from_lesson - 1 : to_lesson]:
        lesson = requests.get(lesson["url"], headers=header).json()
        lesson_id = lesson["id"]

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/"

        audio = open(path.join("audios", audio_path), "rb")
        files = {"audio": audio}

        r = requests.patch(postAddress, headers=header, files=files)

        if r.status_code == 400:
            print(r.text)
            exit()

        print(f"Patched audio for: {lesson['title']}")

        time.sleep(sleep)


def patchText(collection, from_lesson, to_lesson, sleep=0):
    texts_folder = "/Users/rafa/Desktop/lingq/post/split"  # nice hardcoded path
    texts = readGreekNumerals(texts_folder)

    for text_filename, lesson in list(zip(texts[1:], collection["lessons"][2:]))[
        from_lesson - 1 : to_lesson
    ]:
        lesson = requests.get(lesson["url"], headers=header).json()
        lesson_id = lesson["id"]

        text = open(path.join(texts_folder, text_filename), "r").read()

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/resplit/"

        m = MultipartEncoder([("text", text)])

        h = {"Authorization": "Token " + key, "Content-Type": m.content_type}

        r = requests.post(postAddress, headers=h, data=m)

        if r.status_code == 400:
            print(r.text)
            exit()

        print(f"Patched text for: {lesson['title']}")

        time.sleep(sleep)


def main():
    # audios_folder = "audios"
    # audios = read(audios_folder)

    url = f"{API_URL_V2}{language_code}/collections/{pk}"
    collection = requests.get(url=url, headers=header).json()

    # patchBlankAudio(collection, 1, 1)
    patchText(collection, 1, 13, 1)


if __name__ == "__main__":
    main()
