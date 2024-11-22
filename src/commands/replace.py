import asyncio

from lingqhandler import LingqHandler
from utils import double_check, timing


async def replace_async(lang: str, course_id: int, replacements: dict[str, str]) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        msg = "\n".join(f"{k} => {v}" for k, v in replacements.items())
        double_check(f"Replacing chars for course: {collection_title}\n{msg}")
        tasks = [handler.replace(lesson.id, replacements) for lesson in lessons]
        await asyncio.gather(*tasks)


@timing
def replace(
    lang: str,
    course_id: int,
    replacements: dict[str, str],
) -> None:
    """Replace text in a course."""
    asyncio.run(replace_async(lang, course_id, replacements))


if __name__ == "__main__":
    # Defaults for manually running this script.
    replace(
        lang="ja",
        course_id=537808,
        replacements={"か": "が"},
    )
