import asyncio
import os
import re
from typing import Any, Tuple

from lingqhandler import LingqHandler
from utils import timing  # type: ignore

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"
DOWNLOAD_FOLDER = "src/downloads"


def get_title_from_lesson(lesson_json: Any) -> str:
    # Implement your own logic to get the picture title from the lesson.
    title = lesson_json["title"]
    author_name = title.split("-")[-1]
    # Pattern to NOT match Hiragana, Katakana, Kanji, and common punctuation/symbols
    non_japanese_pattern = r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uff00-\uffef]"
    author_name = re.sub(non_japanese_pattern, "", author_name)
    return author_name


async def get_picture(handler: LingqHandler, lesson_json: Any) -> Tuple[str, Any]:
    picture_title = get_title_from_lesson(lesson_json)
    lesson = await handler.get_lesson_from_url(lesson_json["url"])
    image_url = lesson["originalImageUrl"]
    response = await handler.session.get(image_url)
    picture_content = await response.content.read()
    return (picture_title, picture_content)


async def get_pictures(language_code: str, course_id: str) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        collection_title = collection_json["title"]
        tasks = [get_picture(handler, lesson_json) for lesson_json in collection_json["lessons"]]
        pictures_and_titles = await asyncio.gather(*tasks)

        os.makedirs(f"{DOWNLOAD_FOLDER}/{collection_title}", exist_ok=True)
        for picture_title, picture_content in pictures_and_titles:
            with open(f"{DOWNLOAD_FOLDER}/{collection_title}/{picture_title}.png", "wb") as f:
                f.write(picture_content)


@timing
def main():
    asyncio.run(get_pictures(LANGUAGE_CODE, COURSE_ID))


if __name__ == "__main__":
    main()
