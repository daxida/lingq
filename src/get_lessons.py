import asyncio
import os
from typing import Any

from get_lesson import Lesson, get_lesson, sanitize_title, write_lesson
from lingqhandler import LingqHandler
from utils import timing  # type: ignore


def write_lessons(
    language_code: str,
    lessons: list[Lesson],
    download_folder: str,
    verbose: bool,
) -> None:
    for idx, lesson in enumerate(lessons, 1):
        if verbose:
            print(f"Writing lesson nº{idx}: {lesson.title}")
        write_lesson(language_code, lesson, download_folder)


def filter_already_downloaded(texts_folder: str, lessons: Any, verbose: bool) -> Any:
    if not os.path.exists(texts_folder):
        return lessons

    text_files = os.listdir(texts_folder)
    filtered_lessons = [
        lesson for lesson in lessons if f"{sanitize_title(lesson['title'])}.txt" not in text_files
    ]
    if verbose:
        print(
            f"Skipped {len(lessons) - len(filtered_lessons)} out of {len(lessons)} lessons that were already downloaded."
        )
    return filtered_lessons


async def _get_lessons(
    language_code: str,
    course_id: str,
    skip_already_downloaded: bool,
    download_audio: bool,
    download_timestamps: bool,
    download_folder: str,
    write: bool,
    verbose: bool,
) -> tuple[str, list[Lesson]]:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        collection_title = collection_json["title"]
        lessons = collection_json["lessons"]

        at_url = (
            f" at https://www.lingq.com/learn/{language_code}/web/library/course/{course_id}"
            if verbose
            else ""
        )
        print(f"Getting: '{collection_title}'{at_url}")

        if skip_already_downloaded:
            texts_folder = os.path.join(download_folder, language_code, collection_title, "texts")
            lessons = filter_already_downloaded(texts_folder, lessons, verbose)

        tasks = [
            get_lesson(
                handler,
                lesson_json["id"],
                download_audio,
                download_timestamps,
                verbose,
            )
            for lesson_json in lessons
        ]
        lessons = await asyncio.gather(*tasks)

        if write:
            write_lessons(language_code, lessons, download_folder, verbose)

        return collection_title, lessons


@timing
def get_lessons(
    language_code: str,
    course_id: str,
    skip_already_downloaded: bool,
    download_audio: bool,
    download_timestamps: bool,
    download_folder: str,
    write: bool,
    verbose: bool,
) -> None:
    """
    Downloads text and/or audio from a course given the language code and the course ID.

    Args:
        language_code (str): The language code of the course.
        course_id (str): The ID of the course. This is the last number in the course URL.
        skip_already_downloaded (bool): If True, skip downloading already downloaded lessons.
        download_audio (bool): If True, downloads the audio files for the lessons.
        download_folder (str): The folder where the downloaded text and audio files will be saved.

    Creates a 'download' folder and saves the text/audio in 'text'/'audio' subfolders.
    """
    _collection_title, _lessons = asyncio.run(
        _get_lessons(
            language_code,
            course_id,
            skip_already_downloaded,
            download_audio,
            download_timestamps,
            download_folder,
            write,
            verbose,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_lessons(
        language_code="el",
        course_id="730129",
        skip_already_downloaded=False,
        download_audio=True,
        download_timestamps=True,
        download_folder="downloads",
        write=True,
        verbose=True,
    )
