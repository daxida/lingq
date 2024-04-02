import os
import time
from os import path

from natsort import os_sorted
from typing import Any, List
from utils import LingqHandler

# from requests_toolbelt.multipart.encoder import MultipartEncoder

# This deals with overwriting of existing lessons / collections.
# The main usecase is to add audio to an already uploaded book where some
# editing has already be done, and we wouldn't want to upload the text again.

# The blank audios were found here: https://github.com/anars/blank-audio

# Change these two. Pk is the id of the collection
# pk = "1070313" # Quick imports
LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

AUDIOS_FOLDER = "audios"
SLEEP_SECONDS = 0


# TODO: implement the changes from the updated "post.py" script
def read(folder: str) -> List[str]:
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


def patch_blank_audio(
    handler: LingqHandler, collection: Any, from_lesson: int, to_lesson: int
) -> None:
    print(
        f"Patching blank audio for course: {COURSE_ID}, in language: {LANGUAGE_CODE} (lessons {from_lesson} to {to_lesson})"
    )
    double_check()

    lesson_iter = handler.iter_lessons_from_collection(collection, from_lesson, to_lesson)
    lessons = list(lesson_iter)
    max_iterations = len(lessons)
    blank_audio_path = os.path.join(AUDIOS_FOLDER, "15-seconds-of-silence.mp3")

    for idx, lesson in enumerate(lessons, 1):
        audio_files = {"audio": open(blank_audio_path, "rb")}

        response = handler.patch_audio(LANGUAGE_CODE, lesson["id"], audio_files)
        if response.status_code != 200:
            print(f"Error in patch blank audio for lesson: {lesson['title']}")

        print(f"[{idx}/{max_iterations}] Patched audio for: {lesson['title']}")
        time.sleep(SLEEP_SECONDS)

    print("patch_blank_audio finished!")


def patch_bulk_audios(
    handler: LingqHandler, collection: Any, audios_path: List[str], from_lesson: int, to_lesson: int
) -> None:
    lesson_iter = handler.iter_lessons_from_collection(collection, from_lesson, to_lesson)
    lessons = list(lesson_iter)
    max_iterations = len(lessons)

    # Confirm the patching
    for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
        print(f"{audio_path} -> {lesson['title']}")
    double_check()

    for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
        audio_path = path.join(AUDIOS_FOLDER, audio_path)
        audio_files = {"audio": open(audio_path, "rb")}

        response = handler.patch_audio(LANGUAGE_CODE, lesson["id"], audio_files)
        if response.status_code != 200:
            print(f"Error in patch blank audio for lesson: {lesson['title']}")

        print(f"[{idx}/{max_iterations}] Patched audio for: {lesson['title']}")
        time.sleep(SLEEP_SECONDS)

    print("patch_bulk_audios finished!")


def resplit_japanese(handler: LingqHandler, collection: Any, from_lesson: int, to_lesson: int):
    """
    Re-split an existing lesson in japanese with ichimoe.
    Cf: https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754
    """

    assert LANGUAGE_CODE == "ja"
    print(
        f"Resplitting text for course: {COURSE_ID}, in language: {LANGUAGE_CODE} (lessons {from_lesson} to {to_lesson})"
    )
    double_check()

    for lesson in handler.iter_lessons_from_collection(collection, from_lesson, to_lesson):
        response = handler.resplit_lesson(LANGUAGE_CODE, lesson["id"], method="ichimoe")
        if response.status_code != 200:
            print(f"Error in patch blank text for lesson: {lesson['title']}")
            return

        print(f"Resplit text for: {lesson['title']}")
        time.sleep(SLEEP_SECONDS)


def main():
    handler = LingqHandler()

    audios_path = read(AUDIOS_FOLDER)

    collection = handler.get_collection_from_id(LANGUAGE_CODE, COURSE_ID)

    patch_blank_audio(handler, collection, 1, 3)
    # patch_bulk_audios(handler, collection, audios_path, 1, 2)
    # resplit_japanese(handler, collection, 1, 2)


if __name__ == "__main__":
    main()
