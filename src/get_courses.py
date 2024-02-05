import json
import os
import sys

import requests
from dotenv import dotenv_values
from utils import Collection
from typing import Dict, List

# Given a language code print the fetched collections (courses) as "Collection" objects
# This script is just to explore the API

# TODO: Download everything locally
# TODO: Replace the Collection class with just a JSON

# Assumes that .env is on the root
parent_dir = os.path.dirname(os.getcwd())
env_path = os.path.join(parent_dir, ".env")
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {"Authorization": f"Token {KEY}"}

LANGUAGE_CODE = "fr"

# V3 or V2 it doesn't change for requesting my collections
API_URL_V3 = "https://www.lingq.com/api/v2/"
EDITOR_URL = f"https://www.lingq.com/en/learn/{LANGUAGE_CODE}/web/editor/courses/"


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def get_all_courses() -> List[Dict]:
    url = f"{API_URL_V3}{LANGUAGE_CODE}/collections/my/"
    response = requests.get(url=url, headers=headers)
    my_collections = response.json()

    return my_collections["results"]


def main():
    courses = get_all_courses()

    print(f"Found {len(courses)} courses in language: {LANGUAGE_CODE}")

    for col in courses:
        col_title = col["title"]
        col_id = col["id"]
        url = f"{API_URL_V3}{LANGUAGE_CODE}/collections/{col_id}"
        response = requests.get(url=url, headers=headers)
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
