import asyncio

from lingqhandler import LingqHandler

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"


async def generate_timestamps(language_code: str, course_id: str) -> None:
    async with LingqHandler(language_code) as handler:
        collection_json = await handler.get_collection_json_from_id(course_id)
        collection_title = collection_json["title"]
        lessons = collection_json["lessons"]
        tasks = [handler.generate_timestamps(lesson) for lesson in lessons]
        await asyncio.gather(*tasks)
        print(f"Generated timestamps for '{collection_title}'.")


def main():
    asyncio.run(generate_timestamps(LANGUAGE_CODE, COURSE_ID))


if __name__ == "__main__":
    main()
