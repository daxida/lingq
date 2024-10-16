import asyncio
from typing import Any

from lingqhandler import LingqHandler
from utils import double_check, timing  # type: ignore


async def resplit_japanese(handler: LingqHandler, lessons: list[Any]) -> None:
    """
    Re-split an existing lesson in japanese with ichimoe. Cf:
    https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754
    """
    tasks = [handler.resplit_lesson(lesson, method="ichimoe") for lesson in lessons]
    await asyncio.gather(*tasks)


async def _resplit(course_id: str) -> None:
    async with LingqHandler("ja") as handler:
        collection = await handler.get_collection_json_from_id(course_id)
        lesson_jsons = collection["lessons"]
        double_check(f"Resplitting course: {collection['title']}")
        urls = [lesson_json["url"] for lesson_json in lesson_jsons]
        lessons = await handler.get_lessons_from_urls(urls)
        await resplit_japanese(handler, lessons)


@timing
def resplit(course_id: str) -> None:
    asyncio.run(_resplit(course_id))


if __name__ == "__main__":
    # Defaults for manually running this script.
    resplit(course_id="537808")
