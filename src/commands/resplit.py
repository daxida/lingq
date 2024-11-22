import asyncio

from lingqhandler import LingqHandler
from utils import double_check, timing


async def resplit_async(course_id: int) -> None:
    """Re-split an existing lesson in japanese with ichimoe.

    https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754
    """
    async with LingqHandler("ja") as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        double_check(
            f"Resplitting words for course: {collection_title}\n"
            "WARN: There is currently a bug in lingq that modifies certains characters.\n"
            "      Be sure you have read:\n"
            "      https://forum.lingq.com/t/bug-japanese-re-split-modifies-sentence-quotes/412810"
        )
        tasks = [handler.resplit_lesson(lesson.id, method="ichimoe") for lesson in lessons]
        await asyncio.gather(*tasks)


@timing
def resplit(course_id: int) -> None:
    asyncio.run(resplit_async(course_id))


if __name__ == "__main__":
    # Defaults for manually running this script.
    resplit(course_id=537808)
