import asyncio

from loguru import logger

from lingq.lingqhandler import LingqHandler
from lingq.utils import double_check, timing


async def replace_async(
    lang: str, course_id: int, replacements: dict[str, str], assume_yes: bool
) -> None:
    msg = "\n".join(f"{k} => {v}" for k, v in replacements.items())
    logger.info(msg)

    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        double_check(f"Replacing chars for course: {collection_title}\n{msg}", assume_yes)
        tasks = [handler.replace(lesson.id, replacements) for lesson in lessons]
        await asyncio.gather(*tasks)


@timing
def replace(
    lang: str,
    course_id: int,
    replacements: dict[str, str],
    assume_yes: bool,
) -> None:
    """Replace text in a course."""
    asyncio.run(replace_async(lang, course_id, replacements, assume_yes))


if __name__ == "__main__":
    # Defaults for manually running this script.
    replace(
        lang="ja",
        course_id=537808,
        replacements={"か": "が"},
        assume_yes=False,
    )
