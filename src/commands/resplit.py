import asyncio

from lingqhandler import LingqHandler
from utils import double_check, timing


async def resplit_lesson(handler: LingqHandler, lesson_id: int) -> None:
    """The replacements are necessary due to a bug on LingQ's side
    that affects the characters in 'to_ignore'.
    """
    to_ignore = "『』「」"
    replacements = {k: f"__DUMMY_{idx}__" for idx, k in enumerate(to_ignore)}
    replacements_inv = {v: k for k, v in replacements.items()}

    await handler.replace(lesson_id, replacements)
    await handler.resplit_lesson(lesson_id, method="ichimoe")
    await asyncio.sleep(60)  # Wait for the resplit to finish
    await handler.replace(lesson_id, replacements_inv)


async def resplit_async(course_id: int) -> None:
    """Re-split an existing lesson in japanese with ichimoe. Cf:
    https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754
    """
    async with LingqHandler("ja") as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        double_check(f"Resplitting words for course: {collection_title}")
        tasks = [resplit_lesson(handler, lesson.id) for lesson in lessons]
        await asyncio.gather(*tasks)


@timing
def resplit(course_id: int) -> None:
    asyncio.run(resplit_async(course_id))


if __name__ == "__main__":
    # Defaults for manually running this script.
    resplit(course_id=537808)
