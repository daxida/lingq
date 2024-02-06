from utils import Collection, LingqHandler

# Given a language code print the fetched collections (courses) as "Collection" objects

# TODO: Download everything locally
# TODO: Replace the Collection class with just a JSON

LANGUAGE_CODE = "fr"


def main():
    handler = LingqHandler()
    collections = handler.get_all_collections(LANGUAGE_CODE)

    print(f"Found {len(collections)} courses in language: {LANGUAGE_CODE}")

    for col in collections:
        col = handler.get_collection_from_id(LANGUAGE_CODE, col["id"])

        collection = Collection()
        collection.language_code = LANGUAGE_CODE
        collection.add_data(col)

        print(collection)


if __name__ == "__main__":
    main()
