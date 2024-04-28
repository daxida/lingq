import asyncio
import os
from typing import Any, List, Tuple

from lingqhandler import LingqHandler
from utils import timing  # type: ignore

# Downloads audio / text from a Collection (=Course) given the language code and the ID.
# The ID is just the last number you see when you open a course in the web.
# > In https://www.lingq.com/en/learn/el/web/library/course/1289772 the ID is 1289772

# Creates a 'download' folder and saves the text/audio in a 'text'/'audio' folder.

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"
DOWNLOAD_FOLDER = "downloads"
SKIP_ALREADY_DOWNLOADED = False

# A simple lesson type: (title, text, audio)
Lesson = Tuple[str, List[str], bytes | None]


def sanitize_title(title: str) -> str:
    return title.replace("/", "-")


async def get_lesson(handler: LingqHandler, lesson_json: Any, idx: int) -> Lesson:
    title = lesson_json["title"]
    # title = f"{idx}.{lesson['title']}" # add indices

    lesson_text_json = await handler.get_lesson_from_url(lesson_json["url"])
    text = []
    for token in lesson_text_json["tokenizedText"]:
        paragraph = " ".join(line["text"] for line in token)
        text.append(paragraph)  # type: ignore

    # The audio doesn't need the lesson_text_json
    audio = await handler.get_audio_from_lesson(lesson_json)

    lesson: Lesson = (title, text, audio)
    print(f"Downloaded lesson nº{idx}: {lesson_json['title']}")

    return lesson


def write_lessons(language_code: str, collection_title: str, lessons: List[Lesson]) -> None:
    texts_folder = os.path.join(DOWNLOAD_FOLDER, language_code, collection_title, "texts")
    audios_folder = os.path.join(DOWNLOAD_FOLDER, language_code, collection_title, "audios")

    os.makedirs(texts_folder, exist_ok=True)
    os.makedirs(audios_folder, exist_ok=True)

    for idx, (title, text, audio) in enumerate(lessons, 1):
        sanitized_title = sanitize_title(title)

        if audio:
            mp3_path = os.path.join(audios_folder, f"{sanitized_title}.mp3")
            with open(mp3_path, "wb") as audio_file:
                audio_file.write(audio)

        txt_path = os.path.join(texts_folder, f"{sanitized_title}.txt")
        with open(txt_path, "w", encoding="utf-8") as text_file:
            text_file.write("\n".join(text))

        print(f"Writing lesson nº{idx}: {title}")


async def get_lessons(language_code: str, course_id: str, skip_already_downloaded: bool) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert collection_json is not None
        collection_title = collection_json["title"]
        lessons = collection_json["lessons"]

        print(
            f"Downloading: '{collection_title}' at https://www.lingq.com/learn/{language_code}/web/library/course/{course_id}"
        )

        texts_folder = os.path.join(DOWNLOAD_FOLDER, language_code, collection_title, "texts")
        if skip_already_downloaded and os.path.exists(texts_folder):
            text_files = os.listdir(texts_folder)
            filtered_lessons = [
                lesson
                for lesson in lessons
                if f"{sanitize_title(lesson['title'])}.txt" not in text_files
            ]
            print(
                f"Skipped {len(lessons) - len(filtered_lessons)} out of {len(lessons)} lessons that were already downloaded."
            )
            lessons = filtered_lessons

        tasks = [
            get_lesson(handler, lesson_json, idx) for idx, lesson_json in enumerate(lessons, 1)
        ]
        lessons = await asyncio.gather(*tasks)

        write_lessons(language_code, collection_title, lessons)

        print("Finished download.")


@timing
def main():
    asyncio.run(get_lessons(LANGUAGE_CODE, COURSE_ID, SKIP_ALREADY_DOWNLOADED))


if __name__ == "__main__":
    main()
