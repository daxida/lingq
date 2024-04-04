import asyncio

from lingqhandler import LingqHandler
from utils import timing  # type: ignore

# Given a language code print the fetched collections (courses) as "Collection" objects

# TODO: Download everything locally
# TODO: Replace the Collection class with just a JSON

LANGUAGE_CODE = "fr"


async def get_collections():
    async with LingqHandler(LANGUAGE_CODE) as handler:
        # This is only for the courses ID, since in order to get the text we need
        # to do yet another requests handled through `get_collection_from_id`
        collections_json = await handler.get_my_collections()

        print(f"Found {len(collections_json)} courses in language: {LANGUAGE_CODE}")

        tasks = [
            handler.get_collection_object_from_id(collection["id"])
            for collection in collections_json
        ]
        collections = await asyncio.gather(*tasks)

        for collection in collections:
            print(collection)


@timing
def main():
    asyncio.run(get_collections())


if __name__ == "__main__":
    main()
