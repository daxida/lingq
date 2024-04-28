import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

from aiohttp import ClientResponse, ClientSession
from collection import Collection
from dotenv import find_dotenv, dotenv_values


class Config:
    def __init__(self):
        env_path = find_dotenv()
        if not env_path:
            raise EnvironmentError("Could not find .env file.")
        config = dotenv_values(env_path)

        self.key = config["APIKEY"]
        self.headers = {"Authorization": f"Token {self.key}"}


def E(my_json: Any):
    json.dump(my_json, sys.stdout, ensure_ascii=False, indent=2)


def response_debug(response: ClientResponse, function_name: str, lesson: Optional[Any] = None):
    print(f"Error in {function_name}")
    if lesson is not None:
        print(f"For lesson: {lesson['title']}")
    print(f"Response code: {response.status}")
    print(f"Response text: {response.text}")
    # exit(0)


class LingqHandler:
    """
    NOTE: A collection is a course in the API lingo. It is a group of lessons.

    This abstracts all the requests sent to the LingQ API.
    """

    API_URL_V2 = "https://www.lingq.com/api/v2/"
    API_URL_V3 = "https://www.lingq.com/api/v3/"

    def __init__(self, language_code: str) -> None:
        self.language_code = language_code
        self.config = Config()
        self.session = ClientSession()

    # Make the handler into an async context manager (for better debug messages)
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, tb):  # type: ignore
        await self.session.close()

    async def get_language_codes(self) -> List[str]:
        """Returns a list of language codes with known words"""
        url = f"{LingqHandler.API_URL_V2}languages"
        async with self.session.get(url, headers=self.config.headers) as response:
            languages = await response.json()
            codes = [lan["code"] for lan in languages if lan["knownWords"] > 0]

        return codes

    async def get_lesson_from_url(self, url: str) -> Any:
        """Return a JSON with the lesson, from its url."""
        async with self.session.get(url, headers=self.config.headers) as response:
            lesson = await response.json()

        return lesson

    async def get_lessons_from_urls(self, urls: List[str]) -> List[Any]:
        tasks = [self.get_lesson_from_url(url) for url in urls]
        lessons = await asyncio.gather(*tasks)

        return lessons

    async def get_audio_from_lesson(self, lesson: Any) -> bytes | None:
        """Get the audio from a lesson. Return None if there is no audio."""
        audio = None
        if lesson["audio"]:
            async with self.session.get(lesson["audio"]) as response:
                audio = await response.read()

        return audio

    async def _get_collections_from_url(self, url: str) -> Any:
        async with self.session.get(url, headers=self.config.headers) as response:
            collections = await response.json()

        assert collections["next"] is None, "We are missing some collections"

        return collections["results"]

    async def get_my_collections(self) -> Any:
        """Return a JSON with all my imported collections."""
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/collections/my/"
        return await self._get_collections_from_url(url)

    async def get_currently_studying_collections(self) -> Any:
        """Return a JSON with all the studied collections (Continue Studying shelf)."""
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/search/?shelf=my_lessons&type=collection&sortBy=recentlyOpened"
        return await self._get_collections_from_url(url)

    async def get_collection_json_from_id(self, collection_id: str) -> Any | None:
        """Return a JSON with the collection from a collection_id."""
        url = f"{LingqHandler.API_URL_V2}{self.language_code}/collections/{collection_id}"

        async with self.session.get(url, headers=self.config.headers) as response:
            collection = await response.json()

        if not "lessons" in collection:
            # I think this is mainly due to an issue with their garbage collection.
            print(f"WARN: Ghost collection with id: {collection_id}")
            return None

        if not collection["lessons"]:
            editor_url = f"https://www.lingq.com/learn/{self.language_code}/web/editor/courses/"
            msg = f"WARN: The collection {collection['title']} at {editor_url}{collection_id} has no lessons, (delete it?)"
            print(msg)

        return collection

    async def get_collection_object_from_id(self, collection_id: str) -> Collection | None:
        """Return a Collection object from a collection_id."""
        collection_data = await self.get_collection_json_from_id(collection_id)
        if collection_data is None:
            return None
        if not collection_data["lessons"]:
            return None
        collection = Collection()
        collection.language_code = self.language_code
        collection.add_data(collection_data)
        return collection

    async def patch(self, lesson: Any, data: Dict[str, Any]) -> ClientResponse:
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/lessons/{lesson['id']}/"
        async with self.session.patch(url, headers=self.config.headers, data=data) as response:
            if response.status != 200:
                response_debug(response, "patch", lesson)
        return response

    async def generate_timestamps(self, lesson: Any) -> ClientResponse:
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/lessons/{lesson['id']}/genaudio/"
        async with self.session.post(url, headers=self.config.headers) as response:
            if response.status == 409:
                # Ok error. Happens if you try to generate timestamps
                # before the previous query has had time to finish.
                print(f"Timestamps are still being generated... ({lesson['title']})")
            elif response.status != 200:
                response_debug(response, "generate_timestamps", lesson)
        return response

    async def post_from_multipart(self, data: Any) -> ClientResponse:
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/lessons/import/"
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status == 524:
                # Ok error. Happens if their servers are overloaded.
                print("Cloudflare timeout (> 100 secs).")
            elif response.status != 201:
                response_debug(response, "post_from_multipart")
        return response

    async def resplit_lesson(self, lesson: Any, method: str) -> ClientResponse:
        """Resplit a Japanese lesson using the new splitting logic.
        Cf: https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754/5"""
        url = f"{LingqHandler.API_URL_V3}{self.language_code}/lessons/{lesson['id']}/resplit/"
        data = {}
        if method == "ichimoe":
            data = {"method": "ichimoe"}
        else:
            raise NotImplementedError(f"Method {method} in resplit_lesson")

        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status == 409:
                print("Already splitting.")
            elif response.status != 200:
                response_debug(response, "resplit_lesson", lesson)
        return response
