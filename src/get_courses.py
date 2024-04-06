import asyncio

from get_lessons import get_lessons
from lingqhandler import LingqHandler
from utils import timing  # type: ignore

# Download all the courses in LANGUAGE_CODE
# OR: do the same for all the languages

LANGUAGE_CODE = "fr"


async def get_collections(language_code: str) -> None:
    async with LingqHandler(language_code) as handler:
        # This is only for the courses ID, since in order to get the text we need
        # to do yet another request handled through `get_collection_from_id`
        collections_json = await handler.get_my_collections()
        print(f"Found {len(collections_json)} courses in language: {language_code}")
        for collection_json in collections_json:
            await get_lessons(language_code, collection_json["id"])
            await asyncio.sleep(1)
        # tasks = [
        #     get_lessons(language_code, collection_json["id"])
        #     for collection_json in collections_json
        # ]
        # await asyncio.gather(*tasks)


async def get_all_collections() -> None:
    async with LingqHandler("Filler") as handler:
        language_codes = await handler.get_language_codes()
        for language_code in language_codes:
            await get_collections(language_code)
            await asyncio.sleep(1)


@timing
def main():
    # asyncio.run(get_collections(LANGUAGE_CODE))
    asyncio.run(get_all_collections())


if __name__ == "__main__":
    main()
