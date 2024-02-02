import sys
import os
import requests
import json
from dotenv import dotenv_values

# Downloads audio / text from a Collection given the language code and the pk.
# The pk is just the last number you see when you open a course in the web.
# In https://www.lingq.com/en/learn/el/web/library/course/1289772 the pk is 1289772

# Creates a 'download' folder and saves the text/audio in a 'text'/'audio' folder

# Change these two. Pk is the id of the collection
language_code = "el"
pk = "1289772"

# Assumes that .env is on the root
PATH = os.getcwd()
parent_dir = os.path.dirname(PATH)
env_path = os.path.join(parent_dir, ".env")
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {"Authorization": f"Token {KEY}"}

# V3 or V2 doesn't change for this script
API_URL_V2 = "https://www.lingq.com/api/v2/"


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def clear_folders(download_folder="downloads"):
    download_folder_path = os.path.join(PATH, download_folder)
    for folder_name in ["texts", "audios"]:
        folder_path = os.path.join(download_folder_path, folder_name)
        for file_name in os.listdir(folder_path):
            file = os.path.join(folder_path, file_name)
            if os.path.isfile(file):
                print("Deleting file:", file)
                os.remove(file)
        print("Folder cleared:", folder_path)


def create_folders(download_folder="downloads"):
    download_folder_path = os.path.join(PATH, download_folder)
    folders = ["texts", "audios"]

    if not os.path.exists(download_folder_path):
        os.mkdir(download_folder_path)
        print("Download folder created:", download_folder_path)

    for folder_name in folders:
        folder_path = os.path.join(download_folder_path, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
            print("Folder created:", folder_path)


def get_lessons(collection, texts_folder, audios_folder):
    for idx, lesson in enumerate(collection["lessons"], start=1):
        title = lesson["title"]
        # To manually add indexes to the files
        # title = f"{idx}.{lesson['title']}"

        if lesson["audio"]:
            mp3_response = requests.get(lesson["audio"])
            mp3_path = os.path.join(audios_folder, f"{title}.mp3")
            with open(mp3_path, "wb") as audio_file:
                audio_file.write(mp3_response.content)

        lesson_response = requests.get(lesson["url"], headers=headers).json()

        text = []
        for token in lesson_response["tokenizedText"]:
            paragraph = " ".join(line["text"] for line in token)
            text.append(paragraph)

        txt_path = os.path.join(texts_folder, f"{title}.txt")
        with open(txt_path, "w", encoding="utf-8") as text_file:
            text_file.write("\n".join(text))

        print(f"Downloaded lesson nº{idx}: {title}")


def main():
    download_folder = "downloads"

    create_folders(download_folder)
    # Uncomment to clear downloads folder before downloading
    # clear_folders()

    texts_folder = os.path.join(PATH, download_folder, "texts")
    audios_folder = os.path.join(PATH, download_folder, "audios")

    url = f"{API_URL_V2}{language_code}/collections/{pk}"
    collection = requests.get(url=url, headers=headers).json()

    print(f"Downloading https://www.lingq.com/en/learn/el/web/library/course/{pk}")
    get_lessons(collection, texts_folder, audios_folder)
    print("Finished download")


if __name__ == "__main__":
    main()
