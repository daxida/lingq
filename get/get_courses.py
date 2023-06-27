import sys
import os
import requests
import json
from myclass import Collection
from dotenv import dotenv_values

# Given a language code, it prints the fetched collections (courses) 
# according to the Collection class

# TODO: Download everything locally
# TODO: Replace the Collection class with just a JSON

# This script is just to explore the API

# Assumes that .env is on the root
parent_dir = os.path.dirname(os.getcwd())
env_path = os.path.join(parent_dir, '.env')
config = dotenv_values(env_path)

KEY = config["APIKEY"]
headers = {'Authorization': f"Token {KEY}"}

# V3 or V2 it doesn't change for requesting my collections
API_URL_V3 = 'https://www.lingq.com/api/v2/'
language_code = 'fr'
base_editor_url = f"https://www.lingq.com/en/learn/{language_code}/web/editor/courses/"


def E(myjson):
    json.dump(myjson, sys.stdout, ensure_ascii=False, indent=2)


def main():
    my_collections = requests.get(
        url=f"{API_URL_V3}{language_code}/collections/my/", 
        headers=headers
    ).json()

    for col in my_collections['results']:
        _id = col['id']
        url = f"{API_URL_V3}{language_code}/collections/{_id}"
        col = requests.get(
            url=url,
            headers=headers
        ).json()

        if len(col['lessons']) == 0:
            raise RuntimeError(
            f"The collection at {base_editor_url}{_id} has no lessons, consider deleting")

        collection = Collection()
        collection.language_code = language_code
        collection.addData(col)

        print(collection)


if __name__ == '__main__':
    main()
