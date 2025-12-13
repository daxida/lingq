import asyncio

from lingq.lingqhandler import LingqHandler
from lingq.utils import double_check, timing


async def resplit_async(lang: str, course_id: int) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return
        collection_title = lessons[0].collection_title
        if lang == "ja":
            double_check(
                f"Resplitting words for course: {collection_title}\n"
                "WARN: There is currently a bug in lingq that modifies certains characters.\n"
                "      Be sure you have read:\n"
                "      https://forum.lingq.com/t/bug-japanese-re-split-modifies-sentence-quotes/412810"
            )
            tasks = [handler.resplit_lesson(lesson.id) for lesson in lessons]
        else:
            lesson = await handler.get_lesson_from_id(lessons[0].id)
            lesson_text = lesson.get_raw_text()
            data = {"text": lesson_text}
            tasks = [handler.resplit_lesson(lesson.id, data) for lesson in lessons]
        await asyncio.gather(*tasks)


@timing
def resplit(lang: str, course_id: int) -> None:
    asyncio.run(resplit_async(lang, course_id))


if __name__ == "__main__":
    # Defaults for manually running this script.
    resplit(
        lang="ja",
        course_id=537808,
    )
