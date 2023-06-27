import sys, time
import os
from os import path
import json
# import roman
from natsort import os_sorted
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from dotenv import dotenv_values

# post_text seems to work but it has been a long time since I tried post_text_and_audio.
# The same goes for patch_text, although now that the limit is 6k words it should be fine.

# The preprocessed split text.txt files should be in texts_folder
# and the same goes for the .mp3 in audios_folder
# This assumes that they are paired in a way that zipping them makes sense.

# Change these:
texts_folder  = "split"
# If you want to post only text, set audios_folder to None
audios_folder = None
# 1-idxed, 1 is the first lesson
from_lesson = 1
to_lesson   = 2

# Time in seconds to wait between requests
sleep = 2 

# pk = "1070313" # Quick imports
language_code = 'el'
pk = "1070313" 

############################################################

# Assumes that .env is on the root
PATH = os.getcwd()
parent_dir = os.path.dirname(PATH)
env_path = os.path.join(parent_dir, '.env')
config = dotenv_values(env_path)

KEY = config["APIKEY"]

postAddress = "https://www.lingq.com/api/v3/el/lessons/import/"

def readGreekNumerals(folder):
    order = ["Α'", "Β'", "Γ'", "Δ'", "Ε'", "ΣΤ'", "Ζ'", "Η'", "Θ'", "Ι'", "ΙΑ'", "ΙΒ'", "ΙΓ'", "ΙΔ'", "ΙΕ'", "ΙΣΤ'", "ΙΖ'"]
    files = [f for f in os.listdir(folder) if path.isfile(path.join(folder, f)) and not f.startswith(".")]
    # Ι'. Η μάχη -> 10
    return sorted(files, key=lambda x: order.index(x.split('.')[0]))
    

def readRomanNumerals(folder):
    files = [f for f in os.listdir(folder) if path.isfile(path.join(folder, f)) and not f.startswith(".")]
    # Chapitre X.mp3 -> X
    return sorted(files, key=lambda x:roman.fromRoman((x.split()[1]).split(".")[0]))


def read(folder):
    '''Returns a human sorted list of non-hidden directories'''
    return [f for f in os_sorted(os.listdir(folder)) if path.isfile(path.join(folder, f)) and not f.startswith(".")]


def post_text(texts_folder, from_lesson, to_lesson, sleep):
    texts  = read(texts_folder)

    for text_filename in texts[from_lesson-1:to_lesson]:
        title = text_filename.replace('.txt', '')

        file_path = os.path.join(texts_folder, text_filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()


        m = MultipartEncoder([
            ('title', title),
            ('text', text),
            ('collection', pk),
            ('save', "true")]   
        )

        headers = {
            'Authorization': f"Token {KEY}",
            'Content-Type': m.content_type
        }

        response = requests.post(
            url=postAddress, 
            data=m, 
            headers=headers
        )
        
        print(f"  Posted text for lesson {title}")
        
        # DEBUG
        if response.status_code != 201:
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")

        time.sleep(sleep)


def post_text_and_audio(texts_folder, audios_folder, from_lesson, to_lesson, sleep):
    # texts  = readRomanNumerals(texts_folder)
    # audios = readRomanNumerals(audios_folder)
    texts  = readGreekNumerals(texts_folder)
    audios = read(audios_folder)

    for text_filename, audio_filename in list(zip(texts, audios))[from_lesson-1:to_lesson]:
        title = text_filename.replace('.txt', '')
        text  = open(path.join(texts_folder, text_filename), 'r').read()
        audio = open(path.join(audios_folder, audio_filename), 'rb')
        
        m = MultipartEncoder([
                    ('title', title),
                    ('text', text),
                    ('collection', pk),
                    ('audio', (audio_filename, audio, 'audio/mpeg')),
                    ('save', "true")]   
                )

        h = {'Authorization': 'Token ' + KEY,
            'Content-Type': m.content_type}
        
        r = requests.post(postAddress, data=m, headers=h)
        
        print(f"Title: {title} - Audio: {audio_filename}")
        print(f"Posted text and audio for lesson {title}")

        time.sleep(sleep)


def patch_text(collection, texts_folder, from_lesson, to_lesson, sleep):
    '''Patches them with text over the 2k words limit'''

    print(f"Patching text!")

    texts = read(texts_folder)

    for text_filename, lesson in list(zip(texts, collection['lessons']))[from_lesson-1:to_lesson]:
        lesson = requests.get(lesson['url'], headers=header).json()
        lesson_id = lesson["id"]

        text = open(path.join(texts_folder, text_filename), 'r').read()

        postAddress = f"https://www.lingq.com/api/v3/{language_code}/lessons/{lesson_id}/resplit/"

        m = MultipartEncoder([('text', text)])

        h = {
          'Authorization': 'Token ' + key,
          'Content-Type': m.content_type
        }

        r = requests.post(postAddress, headers=h, data=m)

        if r.status_code == 400:
            print(r.text)
            exit()
        
        print(f"Patched text for: {lesson['title']}")

        time.sleep(sleep)


def post(texts_folder, audios_folder, from_lesson, to_lesson, sleep):
    if not texts_folder:
        return print("No texts folder declared, exiting!")
    
    edit_address = f"https://www.lingq.com/en/learn/{language_code}/web/editor/courses/{pk}"
    print(f"Starting upload at {edit_address}")

    if audios_folder:
        print(f"Posting text and audio for lessons {from_lesson} to {to_lesson}...")
        post_text_and_audio(texts_folder, audios_folder, from_lesson, to_lesson, sleep=sleep)
    else:
        print(f"Posting text for lessons {from_lesson} to {to_lesson}...")
        post_text(texts_folder, from_lesson, to_lesson, sleep=sleep)


def main():
    post(texts_folder, audios_folder, from_lesson, to_lesson, sleep=sleep)


if __name__ == '__main__':
    main()
    