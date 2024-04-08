import asyncio
import os
from typing import List, Tuple

import aiohttp
from lingqhandler import LingqHandler
from utils import read_sorted_folders, timing  # type: ignore

# The preprocessed split text.txt files should be in TEXTS_FOLDER
# and the same goes for the .mp3 in AUDIOS_FOLDER
# This assumes that they are paired in a way that zipping them makes sense.

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

# Default folder: "split"
TEXTS_FOLDER = "downloads/Japanese childhood/texts"
# Default folder: "audios"
# Set this to None if you want to post only text.
AUDIOS_FOLDER = "downloads/Japanese childhood/audios"
# Set this to None if you want to post only text.
SRT_FOLDER = None

# 1-idxed, 1 is the first lesson.
FR_LESSON = 1
TO_LESSON = 99  # Write an arbitrarily high number to post everything.

# How to pair the files found in TEXTS_FOLDER and AUDIOS_FOLDER.
# "zip": simple zip of files
# "match_exact_titles": Group texts and audios with the same title.
#   This will post texts if no corresponding audio is found,
#   and ignore audios with no corresponding texts.
PAIRING_STRATEGY = "match_exact_titles"

Pairings = List[Tuple[str, str | None]]


async def post_lesson(
    handler: LingqHandler,
    text_filename: str | None = None,
    audio_filename: str | None = None,
    srt_filename: str | None = None,
) -> None:
    title = None
    data = {
        "collection": COURSE_ID,
        "save": "true",
        "description": "Uploaded with https://github.com/daxida/lingq",
    }
    fdata = aiohttp.FormData()
    for key, value in data.items():
        fdata.add_field(key, value)

    if text_filename:
        assert TEXTS_FOLDER is not None
        title = text_filename.replace(".txt", "")
        file_path = os.path.join(TEXTS_FOLDER, text_filename)
        fdata.add_field("title", title)
        fdata.add_field("text", open(file_path, "r", encoding="utf-8").read())

    if srt_filename:
        assert SRT_FOLDER is not None
        title = srt_filename.replace(".srt", "")
        file_path = os.path.join(SRT_FOLDER, srt_filename)
        srt_file = open(file_path, "r", encoding="utf-8").read()
        fdata.add_field("title", title)
        fdata.add_field(
            "file", srt_file, filename="audio.srt", content_type="application/octet-stream"
        )

    if audio_filename:
        assert AUDIOS_FOLDER is not None
        file_path = os.path.join(AUDIOS_FOLDER, audio_filename)
        audio_file = open(file_path, "rb")
        fdata.add_field("audio", audio_file, filename="audio.mp3", content_type="audio/mpeg")

    await handler.post_from_multipart(fdata)
    with_audio = "with audio " if audio_filename else " "
    print(f"  [OK] Posted lesson {with_audio}'{title}.txt'")


async def post_texts(handler: LingqHandler, texts: List[str]):
    for text_filename in texts:
        await post_lesson(handler, text_filename)


def pairing_strategy(strategy: str, texts: List[str], audios: List[str]) -> Pairings:
    if strategy == "zip":
        pairs = list(zip(texts, audios))
        print(f"Found {len(pairs)} pairs of texts ({len(texts)}) / audio ({len(audios)}).")
    elif strategy == "match_exact_titles":
        pairs: Pairings = list()
        matching_audios = 0
        for text_filename in texts:
            audio_filename = None
            matching_audio_filename = text_filename.replace(".txt", ".mp3")
            if matching_audio_filename in audios:
                audio_filename = matching_audio_filename
                matching_audios += 1
            pairs.append((text_filename, audio_filename))
        print(
            f"Found {matching_audios} matching pairs of texts ({len(texts)}) / audio ({len(audios)})."
        )
    else:
        raise NotImplementedError

    return pairs


async def post_texts_and_audios(handler: LingqHandler, texts: List[str], audios: List[str]):
    pairs = pairing_strategy(PAIRING_STRATEGY, texts, audios)
    for text_filename, audio_filename in pairs:
        await post_lesson(handler, text_filename, audio_filename)


async def post_subtitles_and_audios(handler: LingqHandler, subs: List[str], audios: List[str]):
    pairs = pairing_strategy(PAIRING_STRATEGY, subs, audios)
    for srt_filename, audio_filename in pairs:
        await post_lesson(handler, srt_filename=srt_filename, audio_filename=audio_filename)


async def post():
    async with LingqHandler(LANGUAGE_CODE) as handler:
        url = f"https://www.lingq.com/en/learn/{LANGUAGE_CODE}/web/editor/courses/{COURSE_ID}"
        print(f"Starting upload at {url}")

        if TEXTS_FOLDER:
            texts = read_sorted_folders(TEXTS_FOLDER, mode="human")
            texts = texts[FR_LESSON - 1 : TO_LESSON]

            if AUDIOS_FOLDER:
                audios = read_sorted_folders(AUDIOS_FOLDER, mode="human")
                audios = audios[FR_LESSON - 1 : TO_LESSON]
                print(f"Posting text and audio for lessons {FR_LESSON} to {TO_LESSON}...")
                await post_texts_and_audios(handler, texts, audios)
            else:
                print(f"Posting text for lessons {FR_LESSON} to {TO_LESSON}...")
                await post_texts(handler, texts)
        elif SRT_FOLDER:
            assert TEXTS_FOLDER is None
            assert AUDIOS_FOLDER is not None

            subs = read_sorted_folders(SRT_FOLDER, mode="human")
            subs = subs[FR_LESSON - 1 : TO_LESSON]
            audios = read_sorted_folders(AUDIOS_FOLDER, mode="human")
            audios = audios[FR_LESSON - 1 : TO_LESSON]
            print(f"Posting subtitles and audio for lessons {FR_LESSON} to {TO_LESSON}...")
            await post_subtitles_and_audios(handler, subs, audios)


@timing
def main():
    asyncio.run(post())


if __name__ == "__main__":
    main()
