import json
import os

import requests
from dotenv import dotenv_values
from typing import Dict, List

# Downloads audio / text from a Collection given the language code and the pk.
# The pk is just the last number you see when you open a course in the web.
# In https://www.lingq.com/en/learn/el/web/library/course/1289772 the pk is 1289772

# Creates a 'download' folder and saves the text/audio in a 'text'/'audio' folder

# Change these two. Pk (or course_id) is the id of the collection
LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

# Assumes that .env is on the root
PATH = os.getcwd()
parent_dir = os.path.dirname(PATH)
env_path = os.path.join(parent_dir, ".env")
config = dotenv_values(env_path)

KEY = config["APIKEY"]
HEADERS = {"Authorization": f"Token {KEY}"}

DOWNLOAD_FOLDER = "downloads"

# V3 or V2 doesn't change for this script
API_URL_V2 = "https://www.lingq.com/api/v2/"


def E(myjson):
    json.dump(myjson, ensure_ascii=False, indent=2)


def clear_folders():
    for folder_name in ["texts", "audios"]:
        folder_path = os.path.join(DOWNLOAD_FOLDER, folder_name)
        for file_name in os.listdir(folder_path):
            file = os.path.join(folder_path, file_name)
            if os.path.isfile(file):
                print("Deleting file:", file)
                os.remove(file)
        print("Folder cleared:", folder_path)


def create_folders():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.mkdir(DOWNLOAD_FOLDER)
        print("Download folder created:", DOWNLOAD_FOLDER)

    for folder_name in ["texts", "audios"]:
        folder_path = os.path.join(DOWNLOAD_FOLDER, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            print("Folder created:", folder_path)


def get_lessons(collection: Dict) -> List:
    lessons = list()

    for idx, lesson in enumerate(collection["lessons"], 1):
        title = lesson["title"]
        # title = f"{idx}.{lesson['title']}" # add indices

        lesson_response = requests.get(lesson["url"], headers=HEADERS)
        lesson_json = lesson_response.json()

        text = []
        for token in lesson_json["tokenizedText"]:
            paragraph = " ".join(line["text"] for line in token)
            text.append(paragraph)

        audio = None
        if lesson["audio"]:
            audio_response = requests.get(lesson["audio"])
            audio = audio_response.content

        downloaded_lesson = (title, text, audio)
        lessons.append(downloaded_lesson)

        print(f"Downloaded lesson nº{idx}: {title}")

    return lessons


def write_lessons(lessons) -> None:
    texts_folder = os.path.join(DOWNLOAD_FOLDER, "texts")
    audios_folder = os.path.join(DOWNLOAD_FOLDER, "audios")

    for idx, (title, text, audio) in enumerate(lessons, 1):
        if audio:
            mp3_path = os.path.join(audios_folder, f"{title}.mp3")
            with open(mp3_path, "wb") as audio_file:
                audio_file.write(audio)

        txt_path = os.path.join(texts_folder, f"{title}.txt")
        with open(txt_path, "w", encoding="utf-8") as text_file:
            text_file.write("\n".join(text))

        print(f"Writing lesson nº{idx}: {title}")


def main():
    create_folders()
    # Uncomment to clear downloads folder before downloading
    # clear_folders()

    url = f"{API_URL_V2}{LANGUAGE_CODE}/collections/{COURSE_ID}"
    response = requests.get(url=url, headers=HEADERS)
    collection = response.json()

    print(f"Downloading https://www.lingq.com/learn/{LANGUAGE_CODE}/web/library/course/{COURSE_ID}")
    lessons = get_lessons(collection)
    write_lessons(lessons)
    print("Finished download")


if __name__ == "__main__":
    main()
