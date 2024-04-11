import asyncio
from typing import Any, List

from lingqhandler import LingqHandler

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"
SKIP_ALREADY_TIMESTAMPED = True


async def check_if_timestamped(handler: LingqHandler, lesson: Any) -> None:
    lesson_json = await handler.get_lesson_from_url(lesson["url"])
    tokens = lesson_json["tokenizedText"]
    assert len(tokens) > 0 and len(tokens[0]) == 1
    timestamp = tokens[0][0]["timestamp"]
    if timestamp[0] is not None:
        print(f"[skip: already timestamped] {lesson['title']}")
        lesson["is_timestamped"] = True
    else:
        print(f"Generating timestamps for {lesson['title']}")
        lesson["is_timestamped"] = False


async def filter_already_timestamped(handler: LingqHandler, lessons: List[Any]) -> List[Any]:
    tasks = [check_if_timestamped(handler, lesson) for lesson in lessons]
    await asyncio.gather(*tasks)
    return [lesson for lesson in lessons if not lesson["is_timestamped"]]


async def generate_timestamps(language_code: str, course_id: str) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        collection_title = collection_json["title"]
        lessons = collection_json["lessons"]
        if SKIP_ALREADY_TIMESTAMPED:
            lessons = await filter_already_timestamped(handler, lessons)
            if not lessons:
                print("Everything was already timestamped!")
                return
        tasks = [handler.generate_timestamps(lesson) for lesson in lessons]
        await asyncio.gather(*tasks)
        print(f"Generated timestamps for '{collection_title}'.")


def main():
    asyncio.run(generate_timestamps(LANGUAGE_CODE, COURSE_ID))


if __name__ == "__main__":
    main()
