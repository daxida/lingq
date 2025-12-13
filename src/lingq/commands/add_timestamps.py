import asyncio

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.collection_v3 import CollectionLessonResult


async def check_if_timestamped(handler: LingqHandler, lesson_res: CollectionLessonResult) -> bool:
    lesson = await handler.get_lesson_from_id(lesson_res.id)
    is_timestamped = any(lesson.tokenized_text[0][0].timestamp)
    if is_timestamped:
        logger.info(f"[Skip: already timestamped] {lesson.title}")
    return is_timestamped


async def filter_timestamped(
    handler: LingqHandler, lessons: list[CollectionLessonResult]
) -> list[CollectionLessonResult]:
    results = await asyncio.gather(*(check_if_timestamped(handler, lesson) for lesson in lessons))
    return [lesson for lesson, is_timestamped in zip(lessons, results) if not is_timestamped]


async def add_timestamps_async(lang: str, course_id: int, skip_timestamped: bool) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)

        if not lessons:
            return
        if skip_timestamped:
            lessons = await filter_timestamped(handler, lessons)
            if not lessons:
                print("Everything was already timestamped!")
                return
        tasks = [handler.generate_timestamps(lesson.id) for lesson in lessons]
        await asyncio.gather(*tasks)
        logger.info(f"Generated timestamps for '{lessons[0].collection_title}'.")


def add_timestamps(lang: str, course_id: int, skip_timestamped: bool) -> None:
    """Add course timestamps."""
    asyncio.run(add_timestamps_async(lang, course_id, skip_timestamped))


if __name__ == "__main__":
    # Defaults for manually running this script.
    add_timestamps(lang="ja", course_id=537808, skip_timestamped=True)
