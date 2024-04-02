import os
from typing import Any, List, Tuple

from utils import LingqHandler

# Downloads audio / text from a Collection given the language code and the pk.
# The pk is just the last number you see when you open a course in the web.
# In https://www.lingq.com/en/learn/el/web/library/course/1289772 the pk is 1289772

# Creates a 'download' folder and saves the text/audio in a 'text'/'audio' folder

# Change these two. Pk (or course_id) is the id of the collection
LANGUAGE_CODE = "ja"
COURSE_ID = "537808"

DOWNLOAD_FOLDER = "downloads"


# A simple lesson type: (title, text, audio)
Lesson = Tuple[str, List[str], bytes | None]


def get_lessons(handler: LingqHandler, collection: Any) -> List[Lesson]:
    lessons: List[Lesson] = list()

    for idx, lesson in enumerate(collection["lessons"], 1):
        title = lesson["title"]
        # title = f"{idx}.{lesson['title']}" # add indices

        lesson_json = handler.get_lesson_from_url(lesson["url"])
        text = []
        for token in lesson_json["tokenizedText"]:
            paragraph = " ".join(line["text"] for line in token)
            text.append(paragraph)  # type: ignore

        # The audio doesn't need the lesson_json
        audio = handler.get_audio_from_lesson(lesson)

        downloaded_lesson: Lesson = (title, text, audio)
        lessons.append(downloaded_lesson)

        print(f"Downloaded lesson nº{idx}: {title}")

    return lessons


def write_lessons(collection_title: str, lessons: List[Lesson]) -> None:
    texts_folder = os.path.join(DOWNLOAD_FOLDER, collection_title, "texts")
    audios_folder = os.path.join(DOWNLOAD_FOLDER, collection_title, "audios")

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
    handler = LingqHandler()
    collection = handler.get_collection_from_id(LANGUAGE_CODE, COURSE_ID)
    collection_title = collection["title"]

    print(
        f"Downloading: '{collection_title}' at https://www.lingq.com/learn/{LANGUAGE_CODE}/web/library/course/{COURSE_ID}"
    )

    for folder_name in ["audios", "texts"]:
        os.makedirs(os.path.join(DOWNLOAD_FOLDER, collection_title, folder_name), exist_ok=True)

    lessons = get_lessons(handler, collection)
    write_lessons(collection_title, lessons)
    print("Finished download")


if __name__ == "__main__":
    main()
