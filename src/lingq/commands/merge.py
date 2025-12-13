import asyncio

from lingq.lingqhandler import LingqHandler


async def merge_async(
    lang: str,
    fr_course_id: int,
    to_course_id: int,
) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(fr_course_id)
        for lesson in lessons:
            await handler.patch_course(lesson.id, to_course_id)


def merge(
    lang: str,
    fr_course_id: int,
    to_course_id: int,
) -> None:
    """Merge two courses.

    Moves all the lessons from course FR to course TO.

    The old course, even if it remains without any lessons, will not be deleted.
    """
    asyncio.run(merge_async(lang, fr_course_id, to_course_id))


if __name__ == "__main__":
    merge(
        lang="de",
        fr_course_id=2024348,
        to_course_id=600154,
    )
