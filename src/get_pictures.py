import asyncio
import os
import re
from typing import Any

from lingqhandler import LingqHandler
from utils import timing  # type: ignore


def get_title_from_lesson(lesson_json: Any) -> str:
    # Implement your own logic to get the picture title from the lesson.
    title = lesson_json["title"]
    author_name = title.split("-")[-1]
    # Pattern to NOT match Hiragana, Katakana, Kanji, and common punctuation/symbols
    non_japanese_pattern = r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uff00-\uffef]"
    author_name = re.sub(non_japanese_pattern, "", author_name)
    if not author_name:
        author_name = title  # last resort
    return author_name


async def get_picture(handler: LingqHandler, lesson_json: Any) -> tuple[str, Any]:
    picture_title = get_title_from_lesson(lesson_json)
    lesson = await handler.get_lesson_from_url(lesson_json["url"])
    image_url = lesson["originalImageUrl"]
    response = await handler.session.get(image_url)
    picture_content = await response.content.read()
    return (picture_title, picture_content)


async def _get_pictures(language_code: str, course_id: str, download_folder: str) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert collection_json is not None
        collection_title = collection_json["title"]
        print(f"Getting pictures for {collection_title} ({language_code})")
        tasks = [get_picture(handler, lesson_json) for lesson_json in collection_json["lessons"]]
        pictures_and_titles = await asyncio.gather(*tasks)

        collection_folder = os.path.join(download_folder, language_code, collection_title)
        os.makedirs(collection_folder, exist_ok=True)
        for picture_title, picture_content in pictures_and_titles:
            picture_path = os.path.join(collection_folder, f"{picture_title}.png")
            with open(picture_path, "wb") as f:
                f.write(picture_content)


@timing
def get_pictures(language_code: str, course_id: str, download_folder: str):
    """Get all pictures from a course"""
    asyncio.run(_get_pictures(language_code, course_id, download_folder))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_pictures(language_code="ja", course_id="537808", download_folder="downloads")
