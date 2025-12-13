import asyncio
import re
from pathlib import Path
from typing import Any

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.collection_v3 import CollectionLessonResult
from lingq.utils import timing

TitledPicture = tuple[str, Any]


def get_title_from_lesson(lesson_json: CollectionLessonResult) -> str:
    # Implement your own logic to get the image title from the lesson.
    title = lesson_json.title
    author_name = title.split("-")[-1]
    # Pattern to NOT match Hiragana, Katakana, Kanji, and common punctuation/symbols
    non_japanese_pattern = r"[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uff00-\uffef]"
    author_name = re.sub(non_japanese_pattern, "", author_name)
    if not author_name:
        author_name = title  # last resort
    return author_name


async def get_image(handler: LingqHandler, lesson: CollectionLessonResult) -> TitledPicture:
    image_title = get_title_from_lesson(lesson)
    image_url = lesson.original_image_url
    if not image_url:
        raise ValueError(f"No image at lesson {lesson.url}")
    response = await handler.session.get(image_url)
    image_content = await response.content.read()
    return (image_title, image_content)


def write_images(images_and_titles: list[TitledPicture], collection_path: Path) -> None:
    images_path = collection_path / "images"
    Path.mkdir(images_path, parents=True, exist_ok=True)
    for image_title, image_content in images_and_titles:
        image_path = images_path / f"{image_title}.png"
        with image_path.open("wb") as f:
            f.write(image_content)
    logger.success(f"Wrote images at {images_path}")


async def get_images_async(lang: str, course_id: int, opath: Path) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        logger.info(f"Getting images for {collection_title} ({lang})")
        tasks = [get_image(handler, lesson_json) for lesson_json in lessons]
        images_and_titles = await asyncio.gather(*tasks)
        collection_path = opath / lang / collection_title
        write_images(images_and_titles, collection_path)


@timing
def get_images(lang: str, course_id: int, opath: Path) -> None:
    """Get course images."""
    asyncio.run(get_images_async(lang, course_id, opath))


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_images(lang="ja", course_id=537808, opath=Path("downloads"))
