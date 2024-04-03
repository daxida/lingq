import asyncio
import json
import os
import sys
import time
from functools import wraps
from typing import Any, Dict, List

import requests
from aiohttp import ClientResponse, ClientSession
from collection import Collection
from dotenv import dotenv_values
from requests import Response

# fmt: off
RED    = "\033[31m"  # Error
GREEN  = "\033[32m"  # Success
YELLOW = "\033[33m"  # Skips
CYAN   = "\033[36m"  # Timings
RESET  = "\033[0m"
# fmt: on


class Config:
    def __init__(self):
        # TODO: fix -> Assumes the scripts are run in the src folder
        parent_dir = os.path.dirname(os.getcwd())
        env_path = os.path.join(parent_dir, ".env")
        config = dotenv_values(env_path)

        self.key = config["APIKEY"]
        self.headers = {"Authorization": f"Token {self.key}"}


def E(my_json: Any):
    json.dump(my_json, sys.stdout, ensure_ascii=False, indent=2)


class LingqHandler:
    """
    NOTE: A collection is a course in the API lingo. It is a group of lessons.

    This abstracts all the requests sent to the LingQ API.
    """

    API_URL_V2 = "https://www.lingq.com/api/v2/"
    API_URL_V3 = "https://www.lingq.com/api/v3/"

    def __init__(self) -> None:
        self.session = ClientSession()
        self.config = Config()

    # Make the handler into an async context manager (for better debug messages)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, tb):  # type: ignore
        await self.session.close()

    def get_language_codes(self) -> List[str]:
        """Returns a list of language codes with known words"""
        url = f"{LingqHandler.API_URL_V2}languages"
        response = requests.get(url=url, headers=self.config.headers)
        languages = response.json()
        codes = [lan["code"] for lan in languages if lan["knownWords"] > 0]

        return codes

    async def _get_collections_from_url(self, language_code: str, url: str) -> Any:
        async with self.session.get(url, headers=self.config.headers) as response:
            collections = await response.json()

        assert collections["next"] is None, "We are missing some collections"

        return collections["results"]

    async def get_my_collections(self, language_code: str) -> Any:
        """
        Return a json file with all my imported collections in this language.
        """
        url = f"{LingqHandler.API_URL_V3}{language_code}/collections/my/"
        return await self._get_collections_from_url(language_code, url)

    async def get_currently_studying_collections(self, language_code: str) -> Any:
        """
        Return a json file with all the studied collections (Continue Studying shelf) in this language.
        """
        url = f"{LingqHandler.API_URL_V3}{language_code}/search/?shelf=my_lessons&type=collection&sortBy=recentlyOpened"
        return await self._get_collections_from_url(language_code, url)

    async def get_collection_json_from_id(self, language_code: str, collection_id: str) -> Any:
        """Return a JSON file with collection in this language"""
        url = f"{LingqHandler.API_URL_V2}{language_code}/collections/{collection_id}"

        async with self.session.get(url, headers=self.config.headers) as response:
            collection = await response.json()

        if not collection["lessons"]:
            editor_url = f"https://www.lingq.com/learn/{language_code}/web/editor/courses/"
            msg = f"The collection {collection['title']} at {editor_url}{collection_id} has no lessons, (delete it?)"
            print(msg)

        return collection

    async def get_collection_object_from_id(
        self, language_code: str, collection_id: str
    ) -> Collection:
        collection_data = await self.get_collection_json_from_id(language_code, collection_id)
        collection = Collection()
        collection.language_code = language_code
        collection.add_data(collection_data)
        return collection

    async def get_lesson_from_url(self, url: str) -> Any:
        """Return a json file with the lesson, given its url."""
        async with self.session.get(url, headers=self.config.headers) as response:
            lesson = await response.json()

        return lesson

    async def get_lessons_from_urls(self, urls: List[str]) -> List[Any]:
        tasks = [self.get_lesson_from_url(url) for url in urls]
        lessons = await asyncio.gather(*tasks)

        return lessons

    async def get_audio_from_lesson(self, lesson: Any) -> bytes | None:
        """
        From a list of lessons obtained by collection["lessons"], gets the audio
        (if any) given a lesson of that list.
        """
        audio = None
        if lesson["audio"]:
            async with self.session.get(lesson["audio"]) as response:
                audio = await response.read()

        return audio

    async def patch_audio(
        self, language_code: str, lesson: Any, audio_files: Dict[str, Any]
    ) -> None:
        lesson_id = lesson["id"]
        url = f"{LingqHandler.API_URL_V3}{language_code}/lessons/{lesson_id}/"
        # response = requests.patch(url=url, headers=self.config.headers, files=audio_files)
        async with self.session.get(url, headers=self.config.headers, data=audio_files) as response:
            if response.status != 200:
                print(f"Error in patch blank audio for lesson: {lesson['title']}")
                print(f"Response code: {response.status}")
                print(f"Response text: {response.text}")

    async def post_from_multipart(self, language_code: str, data: Any) -> ClientResponse:
        url = f"{LingqHandler.API_URL_V3}{language_code}/lessons/import/"
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status != 201:
                print(f"Response code: {response.status}")
                print(f"Response text: {response.text}")
            return response

    def resplit_lesson(self, language_code: str, lesson_id: str, method: str) -> Response:
        """Returns the response for error management"""
        url = f"{LingqHandler.API_URL_V3}{language_code}/lessons/{lesson_id}/resplit/"
        data = {}
        if method == "ichimoe":
            data = {"method": "ichimoe"}
        else:
            raise NotImplementedError(f"Method {method} in resplit_lesson")

        response = requests.post(url=url, headers=self.config.headers, data=data)

        if response.status_code != 200:
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")

        return response


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"{CYAN}({f.__name__} {te-ts:2.2f}sec){RESET}")
        return result

    return wrap
