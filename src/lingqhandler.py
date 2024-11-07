import asyncio
import sys
from io import BufferedReader
from typing import Any

import aiohttp
from aiohttp import ClientResponse, ClientSession, FormData
from aiohttp_retry import ExponentialRetry, RetryClient
from pydantic import ValidationError

from config import Config
from log import logger
from models.collection import Collection
from models.collection_v3 import (
    CollectionLessonResult,
    CollectionLessons,
    CollectionV3,
    SearchCollectionResult,
    SearchCollections,
)
from models.lesson_v3 import LessonV3
from models.my_collections import MyCollections
from utils import Colors, get_editor_url


class LingqHandler:
    """
    NOTE: A collection is a course in the API lingo. It is a group of lessons.
          For consistency, 'course_id' is prefered over 'collection_id'.

    This abstracts some of the requests sent to the LingQ API.

    Attributes:
        lang (str): The language code for the course (e.g., 'ja' for Japanese).
        config (Config): Configuration settings for the LingQ API.
        session (RetryClient): A retry-enabled HTTP client session.
        _user_id (int | None): The user id. Used for some requests.
    """

    API_URL_V1 = "https://www.lingq.com/api"
    API_URL_V2 = "https://www.lingq.com/api/v2"
    API_URL_V3 = "https://www.lingq.com/api/v3"

    def __init__(self, lang: str) -> None:
        self.lang = lang
        self.config = Config()
        retry_client = RetryClient(
            client_session=ClientSession(),
            raise_for_status=False,
            retry_options=ExponentialRetry(attempts=3),
        )
        self.session = retry_client
        self._user_id = None

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self):  # noqa: ANN204
        return self

    async def __aexit__(self, *_):  # noqa: ANN002, ANN204
        await self.close()

    """Debug utils"""

    async def _options(self, url: str) -> Any:  # noqa: ANN401
        async with self.session.options(url, headers=self.config.headers) as response:
            return await response.json()

    async def response_debug(self, response: ClientResponse) -> None:
        match response.status:
            case 524:
                logger.error("LingQ's servers are overloaded: cloudflare timeout (> 100 secs).")
            case 429:
                logger.error("Rate limited! Slow down and retry in a couple minutes.")
            case 409:
                logger.error("Conflict. Generating timestamps twice?")
            case 404:
                # Not found error.
                pass
            case 401:
                # Invalid APIKEY.
                pass
            case 400:
                # Generic error. Happens for multiple reasons.
                pass
            case _:
                logger.error(f"Unhandled response code error: {response.status}")
        if response.headers.get("Content-Type") == "application/json":
            response_json = await response.json()
            logger.error(f"[{response.status}] Response JSON:\n{response_json}")
        else:
            logger.error(f"Response text: {response.text}")

    """Get requests"""

    async def _get_url(self, url: str, *, params: dict[str, str] = {}) -> Any:  # noqa: ANN401
        logger.trace(f"GET {url}")
        async with self.session.get(url, headers=self.config.headers, params=params) as response:
            if not 200 <= response.status < 300:
                await self.response_debug(response)
            return await response.json()

    async def _get(
        self,
        endpoint: str,
        *,
        version: int = 3,
        add_language: bool = True,
        check_detail: bool = True,
        params: dict[str, str] = {},
    ) -> Any:  # noqa: ANN401
        api_url = {2: LingqHandler.API_URL_V2, 3: LingqHandler.API_URL_V3}[version]
        if add_language:
            url = f"{api_url}/{self.lang}/{endpoint}"
        else:
            url = f"{api_url}/{endpoint}"

        data = await self._get_url(url, params=params)

        if check_detail:
            match data.get("detail", "_SENTINEL"):
                case "_SENTINEL":
                    pass
                case "Invalid token.":
                    logger.error("Invalid APIKEY. Exiting.")
                    sys.exit(1)
                case "Not found.":
                    raise ValueError(f"Not found error at {url=}")
                case _:
                    raise NotImplementedError

        return data

    async def get_user_id(self) -> None:
        """Get and cache the user id."""
        if self._user_id is None:
            data = await self._get_url(f"{LingqHandler.API_URL_V1}/profile/")
            user_id = data["id"]
            logger.trace(f"Cached user id {user_id}")
            self._user_id = user_id

    async def _get_user_langs(self) -> list[str]:
        """Get a list of language codes with known words.
        https://www.lingq.com/apidocs/api-2.0.html#get
        """
        data = await self._get("languages", version=2, add_language=False, check_detail=False)
        return [lc["code"] for lc in data if lc["knownWords"] > 0]

    @classmethod
    def get_user_langs(cls) -> list[str]:
        """Get a list of language codes with known words.
        This is a class method since it does not require initializing a language code.
        """

        async def get_user_langs_tmp() -> list[str]:
            async with cls("Filler") as handler:
                return await handler._get_user_langs()

        return asyncio.run(get_user_langs_tmp())

    async def get_lesson_from_id(self, lesson_id: int) -> LessonV3 | None:
        """Get a lesson, from its id. Example id: 34754329
        Corresponding url: https://www.lingq.com/api/v3/LANG/lessons/ID/
        """
        data = await self._get(f"lessons/{lesson_id}/")
        if reason := data.get("isLocked", ""):
            logger.warning(f"The lesson {lesson_id} is locked: {reason}")
            return None
        lesson = LessonV3.model_validate(data)
        return lesson

    async def get_lesson_from_ids(self, ids: list[int]) -> list[LessonV3 | None]:
        """Get a list of lessons, from their ids."""
        return await asyncio.gather(*(self.get_lesson_from_id(id) for id in ids))

    async def get_collection_lessons_from_id(self, course_id: int) -> list[CollectionLessonResult]:
        """Get a list of lessons, from its id. Example id: 537808
        Corresponding url: https://www.lingq.com/api/v3/ja/collections/537808/lessons
        """
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/collections/{course_id}/lessons/"
        collection_lessons = []
        cur_url = url

        while cur_url:
            res_json = await self._get_url(cur_url)
            try:
                collection_lessons_at_page = CollectionLessons.model_validate(res_json)
            except ValidationError as e:
                print(f"Error at: {cur_url=}")
                raise e
            collection_lessons.extend(collection_lessons_at_page.results)
            cur_url = collection_lessons_at_page.next

        if collection_lessons.count == 0:
            editor_url = get_editor_url(self.lang, course_id, "course")
            print(
                f"{Colors.WARN}WARN{Colors.END}"
                f" The collection {course_id} at {editor_url} has no lessons, (delete it?)"
            )

        return collection_lessons

    async def get_my_collections(self) -> MyCollections:
        data = await self._get("collections/my")
        return MyCollections.model_validate(data)

    async def search(self, params: dict[str, Any]) -> SearchCollections:
        data = await self._get("search", params=params)
        return SearchCollections.model_validate(data)

    async def get_my_collections_shared(self) -> list[SearchCollectionResult]:
        await self.get_user_id()
        data = await self.search(
            {"type": "collection", "sharedBy": str(self._user_id), "sortBy": "recentlyOpened"}
        )
        return data.results

    async def get_currently_studying_collections(self) -> list[SearchCollectionResult]:
        """Get a collection from the 'Continue Studying shelf'.
        This includes collections imported by other users.
        """
        data = await self.search(
            {"shelf": "my_lessons", "type": "collection", "sortBy": "recentlyOpened"}
        )
        return data.results

    async def get_collection_from_id(self, course_id: int) -> CollectionV3:
        data = await self._get(f"collections/{course_id}")
        return CollectionV3.model_validate(data)

    async def get_collection_from_id_v2(self, course_id: int) -> Any:  # noqa: ANN401
        """Returns a JSON. TODO: make a model for it."""
        # check_detail is set to False for the moment because of issues on LingQ's side
        return await self._get(f"collections/{course_id}", version=2, check_detail=False)

    async def get_collection_object_from_id(self, course_id: int) -> Collection | None:
        """Get a custom collection Object from a course_id."""
        collection = await self.get_collection_from_id_v2(course_id)
        if not collection:
            return None
        if collection.get("detail", "") == "Not found.":
            logger.warning(f"Ghost course at: {get_editor_url(self.lang, course_id, "course")}")
            return None
        col = Collection()
        col.add_data(self.lang, collection)
        return col

    async def get_audio_from_lesson(self, lesson: LessonV3) -> bytes | None:
        """Get the audio from a lesson. Return None if there is no audio.
        Note: The key with the audio url is 'audio' in V2 and 'audioUrl' in V3.
        """
        if audio_url := lesson.audio_url:
            async with self.session.get(str(audio_url)) as response:
                return await response.read()

    """Patch requests"""

    ReqReturnType = ClientResponse | Any

    async def _patch(
        self,
        endpoint: str,
        *,
        data: aiohttp.FormData | dict[str, Any] = {},
        raw: bool = False,
        raise_for: dict[int, str] = {},
        warn_for: dict[int, str] = {},
    ) -> ReqReturnType:
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/{endpoint}"
        logger.trace(f"PATCH {url}")
        async with self.session.patch(url, headers=self.config.headers, data=data) as response:
            if msg := raise_for.get(response.status, ""):
                print(msg)
                raise
            if msg := warn_for.get(response.status, ""):
                print(msg)
            if not 200 <= response.status < 300:
                await self.response_debug(response)
                return response
            if raw:
                return response
            return await response.json()

    async def _post(
        self,
        endpoint: str,
        *,
        data: aiohttp.FormData | dict[str, Any] = {},
        raw: bool = False,
        raise_for: dict[int, str] = {},
        warn_for: dict[int, str] = {},
    ) -> ReqReturnType:
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/{endpoint}"
        logger.trace(f"POST {url}")
        async with self.session.post(url, headers=self.config.headers, data=data) as response:
            if msg := raise_for.get(response.status, ""):
                print(msg)
                raise
            if msg := warn_for.get(response.status, ""):
                print(msg)
            if not 200 <= response.status < 300:
                await self.response_debug(response)
                return response
            if raw:
                return response
            return await response.json()

    async def patch_audio(self, lesson_id: int, audio: BufferedReader) -> ClientResponse:
        """PATCH. Replace the audio of a lesson."""
        return await self._patch(f"lessons/{lesson_id}/", data={"audio": audio}, raw=True)

    async def patch_text(self, lesson_id: int, text_data: str) -> ReqReturnType:
        """POST. Replace the text of a lesson.
        Note that this is actually a POST request that works like a patch one.
        """
        return await self._post(f"lessons/{lesson_id}/resplit/", data={"text": text_data})

    async def patch_position(self, lesson_id: int, new_position: int) -> ReqReturnType:
        """PATCH. Replace the position of a lesson in its course."""
        return await self._patch(f"lessons/{lesson_id}", data={"pos": new_position})

    async def generate_timestamps(self, lesson_id: int) -> ReqReturnType:
        """POST. Add timestamps to a lesson."""
        return await self._post(
            f"lessons/{lesson_id}/genaudio/",
            warn_for={405: f"Timestamps are already being generated... (at {lesson_id=})"},
        )

    async def _create_course(self, data: dict[str, Any]) -> ReqReturnType:
        """POST. Create a course."""
        return await self._post("collections/", data=data)

    async def create_course(self, title: str, description: str = "") -> ReqReturnType:
        """Create an empty course given its title and (optional) description.
        Returns the response JSON, which contains an entry "id" for the course id.
        This id can be used for further uploading through post methods.
        """
        return await self._create_course({"title": title, "description": description})

    async def post_from_multipart(self, data: FormData, *, raw: bool = False) -> ReqReturnType:
        return await self._post("lessons/import/", data=data, raw=raw)

    async def post_from_data_dict(
        self, data: dict[str, Any], *, raw: bool = False
    ) -> ReqReturnType:
        """Intended to be used with dictionaries:
        data = {
            "title": "tmp_title",
            "text": "Hello, world!",
            "status": "private",  # default
            "level": 0,           # default
            "collection": course_id,
            "save": True,         # NOTE: This is needed!
        }
        """

        self._check_data_conv(data)
        fdata = FormData(data)
        return await self.post_from_multipart(fdata, raw=raw)

    def _check_data_conv(self, data: dict[str, Any]) -> None:
        """Verify that we have the keys needed by LingQ."""
        needed_keys = {"title", "collection", "save"}
        need_one_of = {"text", "url"}
        keys = set(data.keys())
        if not keys & need_one_of:
            raise ValueError(f"Data needs at least one entry in {need_one_of}")
        for key in needed_keys:
            if key not in data:
                raise ValueError(f"Error at post_from_data_dict: data has no {key=}")

    async def resplit_lesson(self, lesson_id: int, method: str) -> ClientResponse:
        """
        Resplit a Japanese lesson using the new splitting logic.
        Cf: https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754/5
        """
        assert method == "ichimoe", "Only ichimoe is supported atm"
        return await self._post(
            f"lessons/{lesson_id}/resplit/",
            data={"method": method},
            raw=True,
            warn_for={409: f"{Colors.WARN}WARN{Colors.END} Already splitting {lesson_id}"},
        )

    async def delete_course(self, course_id: int) -> None:
        """Crashes if the course is not succesfully deleted."""
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/collections/{course_id}"
        async with self.session.delete(url, headers=self.config.headers) as response:
            assert response.status == 202
