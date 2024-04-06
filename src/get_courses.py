import asyncio

from get_lessons import get_lessons
from lingqhandler import LingqHandler
from utils import timing  # type: ignore

# NOTE: This reorders your 'Continue studying' shelf.
# NOTE: 'Attempt to decode JSON with unexpected mimetype: text/html; charset=utf-8'
#       is probably a timeout issue. Try to slow down the requests by increasing sleep time.
#       (RARE) It can also be due to a 500 error: Internal server error.
#       You should check the lesson itself to see if you can open it in the browser.

# get_collections(LANG): download all 'my imported' courses in LANG.
# get_all_collections(): download all 'my imported' courses in all languages.

LANGUAGE_CODE = "ja"
SLEEP_TIME = 5


async def get_collections(language_code: str) -> None:
    async with LingqHandler(language_code) as handler:
        # This is only for the courses ID, since in order to get the text we need
        # to do yet another request handled through `get_collection_from_id`
        collections_json = await handler.get_my_collections()
        print(f"Found {len(collections_json)} courses in language: {language_code}")
        for collection_json in collections_json:
            await get_lessons(language_code, collection_json["id"], skip_already_downloaded=True)
            await asyncio.sleep(SLEEP_TIME)


async def get_all_collections() -> None:
    async with LingqHandler("Filler") as handler:
        language_codes = await handler.get_language_codes()
        for language_code in language_codes:
            await get_collections(language_code)
            await asyncio.sleep(SLEEP_TIME)


@timing
def main():
    # asyncio.run(get_collections(LANGUAGE_CODE))
    asyncio.run(get_all_collections())


if __name__ == "__main__":
    main()
