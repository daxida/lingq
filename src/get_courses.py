import json
import sys

import requests
from utils import Config, Collection
from typing import Dict, List

# Given a language code print the fetched collections (courses) as "Collection" objects

# TODO: Download everything locally
# TODO: Replace the Collection class with just a JSON

LANGUAGE_CODE = "fr"
EDITOR_URL = f"https://www.lingq.com/en/learn/{LANGUAGE_CODE}/web/editor/courses/"


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def get_all_courses(config: Config) -> List[Dict]:
    url = f"{Config.API_URL_V3}{LANGUAGE_CODE}/collections/my/"
    response = requests.get(url=url, headers=config.headers)
    my_collections = response.json()

    return my_collections["results"]


def main():
    config = Config()
    courses = get_all_courses(config)

    print(f"Found {len(courses)} courses in language: {LANGUAGE_CODE}")

    for col in courses:
        col_title = col["title"]
        col_id = col["id"]
        url = f"{Config.API_URL_V2}{LANGUAGE_CODE}/collections/{col_id}"
        response = requests.get(url=url, headers=config.headers)
        col = response.json()

        if not col["lessons"]:
            msg = f"The collection {col_title} at {EDITOR_URL}{col_id} has no lessons, (delete it?)"
            print(msg)

        collection = Collection()
        collection.language_code = LANGUAGE_CODE
        collection.add_data(col)

        print(collection)


if __name__ == "__main__":
    main()
