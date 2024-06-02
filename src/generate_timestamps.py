import asyncio
from typing import Any

from lingqhandler import LingqHandler
from utils import Colors


async def check_if_timestamped(handler: LingqHandler, lesson: Any) -> None:
    lesson_json = await handler.get_lesson_from_url(lesson["url"])
    tokens = lesson_json["tokenizedText"]
    assert len(tokens) > 0 and len(tokens[0]) == 1
    timestamp = tokens[0][0]["timestamp"]
    if timestamp[0] is not None:
        print(f"{Colors.SKIP}[skip: already timestamped]{Colors.END} {lesson['title']}")
        lesson["is_timestamped"] = True
    else:
        print(f"Generating timestamps for {lesson['title']}")
        lesson["is_timestamped"] = False


async def filter_already_timestamped(handler: LingqHandler, lessons: list[Any]) -> list[Any]:
    tasks = [check_if_timestamped(handler, lesson) for lesson in lessons]
    await asyncio.gather(*tasks)
    return [lesson for lesson in lessons if not lesson["is_timestamped"]]


async def _generate_timestamps(
    language_code: str, course_id: str, skip_already_timestamped: bool
) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        assert collection_json is not None
        collection_title = collection_json["title"]
        lessons = collection_json["lessons"]
        if skip_already_timestamped:
            lessons = await filter_already_timestamped(handler, lessons)
            if not lessons:
                print("Everything was already timestamped!")
                return
        tasks = [handler.generate_timestamps(lesson) for lesson in lessons]
        await asyncio.gather(*tasks)
        print(f"Generated timestamps for '{collection_title}'.")


def generate_timestamps(language_code: str, course_id: str, skip_already_timestamped: bool):
    asyncio.run(_generate_timestamps(language_code, course_id, skip_already_timestamped))


if __name__ == "__main__":
    # Defaults for manually running this script.
    generate_timestamps(language_code="ja", course_id="537808", skip_already_timestamped=True)
