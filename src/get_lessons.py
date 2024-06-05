import asyncio
import os
from dataclasses import dataclass
from typing import Any

from lingqhandler import LingqHandler
from utils import timing  # type: ignore


@dataclass
class Lesson:
    title: str
    url: str
    id_: str
    text: str
    audio: bytes | None


def sanitize_title(title: str) -> str:
    return title.replace("/", "-")


async def get_lesson(
    handler: LingqHandler, lesson_json: Any, idx: int, download_audio: bool, verbose: bool
) -> Lesson:
    title = lesson_json["title"]
    # title = f"{idx}.{lesson['title']}" # add indices
    url = lesson_json["url"]
    id_ = lesson_json["id"]

    lesson_text_json = await handler.get_lesson_from_url(url)

    paragraphs: list[str] = []
    _title, *tokenized_text = lesson_text_json["tokenizedText"]
    for paragraph_data in tokenized_text:
        paragraph: list[str] = []
        for sentence in paragraph_data:
            paragraph.append(sentence["text"])
        paragraphs.append(" ".join(paragraph))
    text = "\n".join(paragraphs)

    if download_audio:
        # The audio doesn't need the lesson_text_json
        audio = await handler.get_audio_from_lesson(lesson_json)
    else:
        audio = None

    lesson = Lesson(title, url, id_, text, audio)
    if verbose:
        print(f"Downloaded lesson nº{idx}: {title}")

    return lesson


def write_lessons(
    language_code: str,
    collection_title: str,
    lessons: list[Lesson],
    download_folder: str,
    verbose: bool,
) -> None:
    texts_folder = os.path.join(download_folder, language_code, collection_title, "texts")
    audios_folder = os.path.join(download_folder, language_code, collection_title, "audios")

    os.makedirs(texts_folder, exist_ok=True)
    os.makedirs(audios_folder, exist_ok=True)

    for idx, lesson in enumerate(lessons, 1):
        sanitized_title = sanitize_title(lesson.title)

        if lesson.audio:
            mp3_path = os.path.join(audios_folder, f"{sanitized_title}.mp3")
            with open(mp3_path, "wb") as audio_file:
                audio_file.write(lesson.audio)

        txt_path = os.path.join(texts_folder, f"{sanitized_title}.txt")
        with open(txt_path, "w", encoding="utf-8") as text_file:
            text_file.write(f"{lesson.title}\n")
            text_file.write(lesson.text)

        if verbose:
            print(f"Writing lesson nº{idx}: {lesson.title}")


async def _get_lessons(
    language_code: str,
    course_id: str,
    skip_already_downloaded: bool,
    download_audio: bool,
    download_folder: str,
    write: bool,
    verbose: bool,
) -> tuple[str, list[Lesson]]:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert collection_json is not None
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
            if os.path.exists(texts_folder):
                text_files = os.listdir(texts_folder)
                filtered_lessons = [
                    lesson
                    for lesson in lessons
                    if f"{sanitize_title(lesson['title'])}.txt" not in text_files
                ]
                if verbose:
                    print(
                        f"Skipped {len(lessons) - len(filtered_lessons)} out of {len(lessons)} lessons that were already downloaded."
                    )
                lessons = filtered_lessons

        tasks = [
            get_lesson(handler, lesson_json, idx, download_audio, verbose)
            for idx, lesson_json in enumerate(lessons, 1)
        ]
        lessons = await asyncio.gather(*tasks)

        if write:
            write_lessons(language_code, collection_title, lessons, download_folder, verbose)

        return collection_title, lessons


@timing
def get_lessons(
    language_code: str,
    course_id: str,
    skip_already_downloaded: bool,
    download_audio: bool,
    download_folder: str,
    write: bool,
    verbose: bool,
):
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
    collection_title, lessons = asyncio.run(
        _get_lessons(
            language_code,
            course_id,
            skip_already_downloaded,
            download_audio,
            download_folder,
            write,
            verbose,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_lessons(
        language_code="ja",
        course_id="537808",
        skip_already_downloaded=False,
        download_audio=False,
        download_folder="downloads",
        write=True,
        verbose=True,
    )
