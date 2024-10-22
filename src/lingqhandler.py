import asyncio
import json
import sys
from io import BufferedReader
from typing import Any

from aiohttp import ClientResponse, ClientSession, FormData
from aiohttp_retry import ExponentialRetry, RetryClient
from dotenv import dotenv_values, find_dotenv
from models.collection import Collection
from utils import Colors


class Config:
    def __init__(self):
        env_path = find_dotenv()
        if not env_path:
            print("Error: could not find an .env file.")
            print("Create an .env file and add the entry: APIKEY='YourLingQAPIKey'")
            print("Exiting.")
            sys.exit(1)

        config = dotenv_values(env_path)
        if "APIKEY" not in config:
            print("Error: the .env file does not contain the LingQ APIKEY.")
            print("Inside the .env file add the entry: APIKEY='YourLingQAPIKey'")
            print("Exiting.")
            sys.exit(1)

        self.key = config["APIKEY"]
        self.headers = {"Authorization": f"Token {self.key}"}


def err(my_json: Any):
    json.dump(my_json, sys.stdout, ensure_ascii=False, indent=2)


async def response_debug(
    response: ClientResponse, function_name: str, lesson: Any | None = None
) -> None:
    print(f"{Colors.FAIL}Error in {function_name}{Colors.END}")
    if lesson is not None:
        print(f"For lesson: {lesson['title']}")
    print(f"Response code: {response.status}")
    if response.headers.get("Content-Type") == "application/json":
        print("Response JSON:")
        response_json = await response.json()
        print(response_json)
    else:
        print(f"Response text: {response.text}")
    # exit(0)


def check_for_valid_token_or_exit(response_json: Any) -> None:
    """Exits the program if the APIKEY is deemed invalid by the server."""
    if isinstance(response_json, dict):
        if response_json.get("detail", "") == "Invalid token.":
            print("Invalid APIKEY. Exiting.")
            sys.exit(1)
    elif isinstance(response_json, list):
        pass
    else:
        raise NotImplementedError(
            f"Unsupported type in check_for_valid_token_or_exit: {type(response_json)}."
        )


class LingqHandler:
    """
    NOTE: A collection is a course in the API lingo. It is a group of lessons.

    This abstracts some of the requests sent to the LingQ API.

    Attributes:
        language_code (str): The language code for the course (e.g., 'ja' for Japanese).
        config (Config): Configuration settings for the LingQ API.
        session (RetryClient): A retry-enabled HTTP client session.
    """

    API_URL_V2 = "https://www.lingq.com/api/v2"
    API_URL_V3 = "https://www.lingq.com/api/v3"

    def __init__(self, language_code: str) -> None:
        self.language_code = language_code
        self.config = Config()
        retry_client = RetryClient(
            client_session=ClientSession(),
            raise_for_status=False,
            retry_options=ExponentialRetry(attempts=3),
        )
        self.session = retry_client

    async def close(self):
        await self.session.close()

    # Make the handler into an async context manager (for better debug messages)
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        await self.close()

    async def get_languages(self) -> Any:
        """
        Get a JSON of supported (or almost) languages by Lingq.
        https://www.lingq.com/apidocs/api-2.0.html#get
        """
        url = f"{LingqHandler.API_URL_V2}/languages"
        async with self.session.get(url, headers=self.config.headers) as response:
            languages_res = await response.json()
            check_for_valid_token_or_exit(languages_res)
        return languages_res

    async def _get_user_language_codes(self) -> list[str]:
        """Get a list of language codes with known words."""
        languages_res = await self.get_languages()
        return [lc["code"] for lc in languages_res if lc["knownWords"] > 0]

    @classmethod
    def get_user_language_codes(cls) -> list[str]:
        """
        Get a list of language codes with known words.
        This is a class method since it does not require initializing a language code.
        """

        async def _get_user_language_codes_tmp():
            async with cls("Filler") as handler:
                return await handler._get_user_language_codes()

        return asyncio.run(_get_user_language_codes_tmp())

    async def get_lesson_from_url(self, url: str) -> Any:
        """
        Get a lesson JSON, from its url.
        Example url: https://www.lingq.com/api/v3/ja/lessons/34754329/
        """
        async with self.session.get(url, headers=self.config.headers) as response:
            lesson = await response.json()
        if lesson.get("isLocked", "") == "TRANSCRIBE_AUDIO":
            print(
                f"{Colors.WARN}WARN{Colors.END} The lesson at {url} is still transcribing audio..."
            )

        return lesson

    async def get_lesson_from_id(self, lesson_id: str) -> Any:
        """Get a lesson JSON, from its id. Example id: 34754329"""
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/{lesson_id}/"
        return await self.get_lesson_from_url(url)

    async def get_lessons_from_urls(self, urls: list[str]) -> list[Any]:
        """Get a list of lesson JSONs, from their urls."""
        return await asyncio.gather(*(self.get_lesson_from_url(url) for url in urls))

    async def get_audio_from_lesson(self, lesson: Any) -> bytes | None:
        """
        Get the audio from a lesson. Return None if there is no audio.
        The key with the audio url is 'audio' in V2 and 'audioUrl' in V3.
        """
        if "audio" in lesson:
            audio_url = lesson["audio"]
        elif "audioUrl" in lesson:
            audio_url = lesson["audioUrl"]
        else:
            raise KeyError("Lesson should have at least an 'audio' or 'audioUrl' key")

        # There is a key but the lesson has no audio
        if audio_url is None:
            return None

        async with self.session.get(audio_url) as response:
            return await response.read()

    async def _get_collections_from_url(self, url: str) -> Any:
        """
        Get a collection JSON, from its url.
        Example urls:
            https://www.lingq.com/api/v3/ja/collections/537808
            https://www.lingq.com/api/v3/ja/collections/my
        """
        async with self.session.get(url, headers=self.config.headers) as response:
            collections = await response.json()

        assert (
            collections.get("detail", "") != "Not found."
        ), f"Error in processing the request at {url=}"
        assert collections["next"] is None, "We are missing some collections"

        results = collections["results"]
        assert results is not None

        return results

    async def get_my_collections(self) -> Any:
        """
        Get a collection JSON with all my imported collections.
        This does not include collections imported by other users.
        """
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/collections/my/"
        return await self._get_collections_from_url(url)

    async def get_currently_studying_collections(self) -> Any:
        """
        Get a collection JSON with all the studied collections (Continue Studying shelf).
        This includes collections imported by other users.
        """
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/search/?shelf=my_lessons&type=collection&sortBy=recentlyOpened"
        return await self._get_collections_from_url(url)

    async def get_collection_json_from_id(self, collection_id: str) -> Any:
        """Get a collection JSON with the collection, from a collection_id."""
        url = f"{LingqHandler.API_URL_V2}/{self.language_code}/collections/{collection_id}/"

        async with self.session.get(url, headers=self.config.headers) as response:
            collection = await response.json()
            check_for_valid_token_or_exit(collection)

        assert collection is not None, "Failed to get collection"

        if "lessons" not in collection:
            # I think this is mainly due to an issue with their garbage collection.
            print(f"{Colors.WARN}WARN{Colors.END} Ghost collection with id: {collection_id}")
            return None

        if not collection["lessons"]:
            editor_url = f"https://www.lingq.com/learn/{self.language_code}/web/editor/courses/"
            msg = f"{Colors.WARN}WARN{Colors.END} The collection {collection['title']} at {editor_url}{collection_id} has no lessons, (delete it?)"
            print(msg)

        return collection

    async def get_collection_object_from_id(self, collection_id: str) -> Collection | None:
        """Get a custom collection Object from a collection_id."""
        collection_data = await self.get_collection_json_from_id(collection_id)
        if not collection_data["lessons"]:
            return None
        collection = Collection()
        collection.language_code = self.language_code
        collection.add_data(collection_data)
        return collection

    async def patch_audio_from_lesson_id(
        self, lesson_id: str, audio_data: BufferedReader
    ) -> ClientResponse:
        """Patch (i.e. replace) the audio of a lesson."""
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/{lesson_id}/"
        data = {"audio": audio_data}
        async with self.session.patch(url, headers=self.config.headers, data=data) as response:
            if response.status != 200:
                await response_debug(response, "patch")
        return response

    async def patch_text_from_lesson_id(self, lesson_id: str, text_data: str) -> ClientResponse:
        """Patch (i.e. replace) the text of a lesson.
        Note that this is actually a post request that works like a patch one."""
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/{lesson_id}/resplit/"
        data = {"text": text_data}
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status != 200:
                await response_debug(response, "patch")
        return response

    async def generate_timestamps(self, lesson: Any) -> ClientResponse:
        """Post request to add timestamps to a lesson."""
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/{lesson['id']}/genaudio/"
        async with self.session.post(url, headers=self.config.headers) as response:
            if response.status == 409:
                # Ok error. Happens if you try to generate timestamps
                # before the previous query has had time to finish.
                print(f"Timestamps are still being generated... ({lesson['title']})")
            elif response.status != 200:
                await response_debug(response, "generate_timestamps", lesson)
        return response

    async def create_course(self, title: str, description: str = "") -> Any:
        """
        Create an empty course given its title and (optional) description.
        Returns the response JSON, which contains an entry "id" for the course id.
        This id can be used for further uploading through post methods.
        """
        return await self._create_course({"title": title, "description": description})

    async def _create_course(self, data: Any) -> Any:
        """
        Create a course from a data payload.
        Returns the response JSON, which contains an entry "id" for the course id.
        This id can be used for further uploading through post methods.

        In its simplest version, it can be called just with the course title:
        handler.create_course({"title": "my_course_title"})

        From: https://github.com/kaajjaak/LingQGPT/
        """
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/collections/"
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status != 201:
                await response_debug(response, "create_course")
            return await response.json()

    async def delete_course(self, course_id: str) -> None:
        """
        Crashes if the course is not succesfully deleted (it is succesfully deleted if
        the response.status is 202) by entering response_debug.
        """
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/collections/{course_id}"
        async with self.session.delete(url, headers=self.config.headers) as response:
            if response.status != 202:
                await response_debug(response, "delete_course")

    async def post_from_multipart(self, data: Any) -> ClientResponse:
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/import/"
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status == 524:
                # Ok error. Happens if their servers are overloaded.
                print("Cloudflare timeout (> 100 secs).")
            elif response.status != 201:
                await response_debug(response, "post_from_multipart")
        return response

    async def post_from_data_dict(self, data: dict[str, Any]) -> ClientResponse:
        """Intended to be used with dictionaries:
        data = {
            "title": "tmp_title",
            "text": "Hello, world!",
            "status": "private",  # default
            "level": 0,  # default
            "collection": course_id,
            "save": True,  # NOTE: This is needed!
        }
        """
        needed_keys = ["title", "text", "collection"]
        warning_keys = ["save"]
        for key in needed_keys:
            if key not in data:
                raise ValueError(f"Error at post_from_data_dict: data has no {key=}")
        for key in warning_keys:
            if key not in data:
                print(f"WARN: at post_from_data_dict: data has no {key=}")

        fdata = FormData()
        for key, value in data.items():
            fdata.add_field(key, value)
        return await self.post_from_multipart(fdata)

    async def resplit_lesson(self, lesson: Any, method: str) -> ClientResponse:
        """
        Resplit a Japanese lesson using the new splitting logic.
        Cf: https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754/5
        """
        url = f"{LingqHandler.API_URL_V3}/{self.language_code}/lessons/{lesson['id']}/resplit/"
        data = {}
        if method == "ichimoe":
            data = {"method": "ichimoe"}
        else:
            raise NotImplementedError(f"Method {method} in resplit_lesson")

        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if response.status == 409:
                print(f"{Colors.WARN}WARN{Colors.END} Already splitting {lesson['title']}")
            elif response.status != 200:
                await response_debug(response, "resplit_lesson", lesson)
        return response
