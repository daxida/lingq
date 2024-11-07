import asyncio
import re
from pathlib import Path
from typing import Any

from lingqhandler import LingqHandler
from models.collection_v3 import CollectionLessonResult
from utils import timing

# TODO: rename to images


TitledPicture = tuple[str, Any]


def get_title_from_lesson(lesson_json: CollectionLessonResult) -> str:
    # Implement your own logic to get the picture title from the lesson.
    title = lesson_json.title
    author_name = title.split("-")[-1]
    # Pattern to NOT match Hiragana, Katakana, Kanji, and common punctuation/symbols
    non_japanese_pattern = r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uff00-\uffef]"
    author_name = re.sub(non_japanese_pattern, "", author_name)
    if not author_name:
        author_name = title  # last resort
    return author_name


async def get_picture(handler: LingqHandler, lesson: CollectionLessonResult) -> TitledPicture:
    picture_title = get_title_from_lesson(lesson)
    image_url = lesson.original_image_url
    if not image_url:
        raise ValueError(f"No picture at lesson {lesson.url}")
    response = await handler.session.get(image_url)
    picture_content = await response.content.read()
    return (picture_title, picture_content)


def write_pictures(pictures_and_titles: list[TitledPicture], collection_path: Path) -> None:
    pictures_path = collection_path / "pictures"
    Path.mkdir(pictures_path, parents=True, exist_ok=True)
    for picture_title, picture_content in pictures_and_titles:
        picture_path = pictures_path / f"{picture_title}.png"
        with picture_path.open("wb") as f:
            f.write(picture_content)
    print(f"Wrote pictures at {pictures_path}")


async def get_pictures_async(lang: str, course_id: int, opath: Path) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        print(f"Getting pictures for {collection_title} ({lang})")
        tasks = [get_picture(handler, lesson_json) for lesson_json in lessons]
        pictures_and_titles = await asyncio.gather(*tasks)
        collection_path = opath / lang / collection_title
        write_pictures(pictures_and_titles, collection_path)


@timing
def get_pictures(lang: str, course_id: int, opath: Path) -> None:
    """Get all pictures from a course"""
    asyncio.run(get_pictures_async(lang, course_id, opath))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_pictures(lang="ja", course_id=537808, opath=Path("downloads"))