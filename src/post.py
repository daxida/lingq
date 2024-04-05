import asyncio
import os
from typing import Any, List

import aiohttp
from lingqhandler import LingqHandler
from utils import read_sorted_folders, timing  # type: ignore

# post_text seems to work but it has been a long time since I tried post_text_and_audio.
# The same goes for patch_text, although now that the limit is 6k words it should be fine.

# The preprocessed split text.txt files should be in texts_folder
# and the same goes for the .mp3 in AUDIOS_FOLDER
# This assumes that they are paired in a way that zipping them makes sense.

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

# Change these:
TEXTS_FOLDER = "split"
# If you want to post only text, set AUDIOS_FOLDER to None
AUDIOS_FOLDER = None
# 1-idxed, 1 is the first lesson.
# Just write an arbitrarily high number in TO_LESSON to post everything.
FR_LESSON = 1
TO_LESSON = 99


async def post_text_in_order(handler: LingqHandler):
    """Use this if you care about the order of the lessons."""
    texts = read_sorted_folders(TEXTS_FOLDER, mode="human")

    to_lesson = min(TO_LESSON, len(texts))
    print(f"Posting text (in order) for lessons {FR_LESSON} to {to_lesson}...")
    texts = texts[FR_LESSON - 1 : to_lesson]

    for text_filename in texts:
        title = text_filename.replace(".txt", "")
        file_path = os.path.join(TEXTS_FOLDER, text_filename)
        data = {
            "title": title,
            "text": open(file_path, "r", encoding="utf-8").read(),
            "collection": COURSE_ID,
            "save": "true",
        }

        await handler.post_from_multipart(data)
        print(f"  Posted text for lesson {title}")


async def post_text_fully_async(handler: LingqHandler):
    """
    Use this if you DONT care about the order of the lessons.
    NOTE: Much faster than post_text_in_order.
    """
    texts = read_sorted_folders(TEXTS_FOLDER, mode="human")

    to_lesson = min(TO_LESSON, len(texts))
    print(f"Posting text for lessons {FR_LESSON} to {to_lesson}...")
    texts = texts[FR_LESSON - 1 : to_lesson]

    data_list: List[Any] = list()
    for text_filename in texts:
        title = text_filename.replace(".txt", "")
        file_path = os.path.join(TEXTS_FOLDER, text_filename)
        data = {
            "title": title,
            "text": open(file_path, "r", encoding="utf-8").read(),
            "collection": COURSE_ID,
            "save": "true",
        }
        data_list.append(data)

    tasks = [handler.post_from_multipart(data) for data in data_list]
    await asyncio.gather(*tasks)


async def post_text_and_audio_in_order(handler: LingqHandler):
    assert AUDIOS_FOLDER is not None

    texts = read_sorted_folders(TEXTS_FOLDER, mode="human")
    audios = read_sorted_folders(AUDIOS_FOLDER, mode="human")

    # NOTE: What if len(texts) != len(audios) ?
    to_lesson = min(TO_LESSON, len(texts))
    print(f"Posting text and audio (in order) for lessons {FR_LESSON} to {to_lesson}...")
    pairs = list(zip(texts, audios))[FR_LESSON - 1 : to_lesson]
    print(f"Found {len(pairs)} pairs of texts ({len(texts)}) / audio ({len(audios)}).")

    for text_filename, audio_filename in pairs:
        title = text_filename.replace(".txt", "")
        text = open(os.path.join(TEXTS_FOLDER, text_filename), "r").read()
        audio_file = open(os.path.join(AUDIOS_FOLDER, audio_filename), "rb")
        data = {
            "title": title,
            "text": text,
            "collection": COURSE_ID,
            "save": "true",
        }

        fdata = aiohttp.FormData()
        for key, value in data.items():
            fdata.add_field(key, value)

        fdata.add_field("audio", audio_file, filename=audio_filename, content_type="audio/mpeg")

        await handler.post_from_multipart(fdata)
        print(f"  Posted text and audio for lesson {title}")


async def post():
    async with LingqHandler(LANGUAGE_CODE) as handler:
        if not TEXTS_FOLDER:
            print("No texts folder declared, exiting!")
            return

        url = f"https://www.lingq.com/en/learn/{LANGUAGE_CODE}/web/editor/courses/{COURSE_ID}"
        print(f"Starting upload at {url}")

        if AUDIOS_FOLDER:
            await post_text_and_audio_in_order(handler)
        else:
            await post_text_in_order(handler)


@timing
def main():
    asyncio.run(post())


if __name__ == "__main__":
    main()
