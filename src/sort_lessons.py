import asyncio
from typing import Any

from lingqhandler import LingqHandler
from utils import timing # type: ignore

# NOTE: Very inefficient if the course is already sorted and
#       we only want to swap a couple lessons.


LANGUAGE_CODE = "ja"
COURSE_ID = "537808"


def sorting_function(lesson: Any):
    return lesson["title"]


async def sort_lessons(language_code: str, course_id: str):
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        lessons = collection_json["lessons"]
        lessons.sort(key=sorting_function)
        for pos, lesson in enumerate(lessons, 1):
            payload = {"pos": pos}
            await handler.patch(lesson, payload)
        print(f"Finished sorting {collection_json['title']}")


@timing
def main():
    asyncio.run(sort_lessons(LANGUAGE_CODE, COURSE_ID))


if __name__ == "__main__":
    main()
