import asyncio
from io import BufferedReader
from typing import Any

from aiohttp import ClientResponse, ClientSession, FormData
from aiohttp_retry import ExponentialRetry, RetryClient

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
from models.counter import Counter
from models.lesson_v3 import LOCKED_REASON_CHOICES, LessonV3
from models.my_collections import MyCollections
from utils import get_editor_url, model_validate_or_exit


class LingqHandler:
    """Abstraction for the requests sent to the LingQ API.

    NOTE: A collection is a course in the API lingo, i.e. a group of lessons.
          For consistency, 'course_id' is prefered over 'collection_id'.

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

    async def __aenter__(self):  # noqa: ANN204
        return self

    async def __aexit__(self, *_):  # noqa: ANN002, ANN204
        await self.session.close()

    """Debug utils"""

    async def _options(self, url: str) -> Any:
        async with self.session.options(url, headers=self.config.headers) as response:
            return await response.json()

    async def response_debug(self, response: ClientResponse) -> None:  # noqa: C901
        match response.status:
            case 524:
                logger.error("LingQ's servers are overloaded: cloudflare timeout (> 100 secs).")
            case 429:
                logger.error("Rate limited! Slow down and retry in a couple minutes.")
            case 409:
                logger.warning("Conflict. Generating timestamps / splitting twice?")
                # Do not print the response text for this error
                return
            case 405:
                logger.warning("Timestamps are already being generated...")
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
            if isinstance(response_json, dict):
                match response_json.get("detail", "_SENTINEL"):
                    case "_SENTINEL":
                        pass
                    case "Invalid token.":
                        raise ValueError("Invalid APIKEY. Exiting.")
                    case _:
                        logger.error("Uncaught detail")
            logger.error(f"[{response.status}] Response JSON:\n{response_json}")
        else:
            logger.error(f"Response text: {response.text}")

    """Generic request"""

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        version: int = 3,
        add_language: bool = True,
        raw: bool = False,
        retry_on_locked: bool = False,
        **kwargs,  # noqa: ANN003
    ) -> Any:
        api_url = {
            1: LingqHandler.API_URL_V1,
            2: LingqHandler.API_URL_V2,
            3: LingqHandler.API_URL_V3,
        }[version]

        if add_language:
            url = f"{api_url}/{self.lang}/{endpoint}"
        else:
            url = f"{api_url}/{endpoint}"

        logger.trace(f"{method.upper()} {url}")
        if params := kwargs.get("params", ""):
            logger.trace(f"{params=}")

        if not retry_on_locked:
            return await self._send_request(method, url, raw=raw, **kwargs)
        else:
            assert raw is False, "Raw must be false when retrying on locked"
            return await self._send_request_retry(method, url, raw=False, **kwargs)

    async def _send_request(
        self,
        method: str,
        url: str,
        *,
        raw: bool,
        quiet: bool = False,
        **kwargs,  # noqa: ANN003
    ) -> Any:
        meth = getattr(self.session, method.lower())
        async with meth(url, headers=self.config.headers, **kwargs) as response:
            if not 200 <= response.status < 300:
                if not quiet:
                    await self.response_debug(response)
                return response
            if raw:
                return response
            return await response.json()

    async def _send_request_retry(
        self,
        method: str,
        url: str,
        *,
        raw: bool,
        max_retries: int = 4,
        **kwargs,  # noqa: ANN003
    ) -> Any:
        """On locked error, retry 'max_retries' times.

        That is, loop until we get a JSON result that does not look like this:
        * {'isLocked': 'TOKENIZE_TEXT', 'errorType': 'locked'}
        * {'isLocked': 'GENERATE_TIMESTAMPS', 'errorType': 'locked'}
        """
        for retry in range(1, max_retries + 1):
            response = await self._send_request(method, url, raw=raw, quiet=True, **kwargs)
            # If _send_request:
            # * failed:    response is a ClientResponse.
            # * succeeded: response was already converted to a json.
            if isinstance(response, ClientResponse):
                response = await response.json()
            if response.get("errorType", "") != "locked":
                return response

            locked_reason = response["isLocked"]
            if locked_reason not in LOCKED_REASON_CHOICES:
                logger.warning(f"Unexpected lock reason: {locked_reason}")
            logger.debug(
                f"Content is locked at {locked_reason}. Retrying... ({retry}/{max_retries})"
            )
            await asyncio.sleep(2**retry)

        raise RuntimeError("Content is locked.")

    """Get requests"""

    async def get_user_id(self) -> None:
        """Get and cache the user id."""
        if self._user_id is None:
            data = await self._request("GET", "profile/", version=1, add_language=False)
            self._user_id = data["id"]
            logger.trace(f"Cached user id {self._user_id}")

    async def _get_user_langs(self) -> list[str]:
        """Get a list of language codes with known words.

        https://www.lingq.com/apidocs/api-2.0.html#get
        """
        data = await self._request("GET", "languages", version=2, add_language=False)
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

    async def get_lesson_from_id(self, lesson_id: int) -> LessonV3:
        """Get a lesson, from its id.

        Example:
            id: 34754329
            url: https://www.lingq.com/api/v3/LANG/lessons/ID/

        """
        data = await self._request(
            "GET",
            f"lessons/{lesson_id}/",
            retry_on_locked=True,
        )
        return LessonV3.model_validate(data)

    async def get_lesson_from_ids(self, ids: list[int]) -> list[LessonV3]:
        """Get a list of lessons, from their ids."""
        return await asyncio.gather(*(self.get_lesson_from_id(id) for id in ids))

    async def get_collection_lessons_from_id(self, course_id: int) -> list[CollectionLessonResult]:
        """Get a list of lessons, from their collection id.

        Example:
            id: 537808
            url: https://www.lingq.com/api/v3/ja/collections/537808/lessons

        """
        base_url_size = len(f"{LingqHandler.API_URL_V3}/{self.lang}/")
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/collections/{course_id}/lessons/"
        collection_lessons = []
        cur_url = url

        while cur_url:
            endpoint = cur_url[base_url_size:]
            res_json = await self._request("GET", endpoint)
            collection_lessons_at_page = CollectionLessons.model_validate(res_json)
            collection_lessons.extend(collection_lessons_at_page.results)
            cur_url = collection_lessons_at_page.next

        if collection_lessons.count == 0:
            editor_url = get_editor_url(self.lang, course_id, "course")
            logger.warning(
                f" The collection {course_id} at {editor_url} has no lessons, (delete it?)"
            )

        return collection_lessons

    async def get_my_collections(self) -> MyCollections:
        data = await self._request("GET", "collections/my")
        return MyCollections.model_validate(data)

    async def counters(self, collection_ids: list[int]) -> dict[str, Counter]:
        """Return summary information about collections."""
        params = {"collection": collection_ids}
        data = await self._request("GET", "collections/counters/", params=params)
        return {
            collection_id: model_validate_or_exit(
                Counter, counter, self.lang, collection_id, "course"
            )
            for collection_id, counter in data.items()
        }

    async def search(self, params: dict[str, Any]) -> SearchCollections:
        data = await self._request("GET", "search", params=params)
        return SearchCollections.model_validate(data)

    async def get_my_collections_shared(self) -> list[SearchCollectionResult]:
        await self.get_user_id()
        data = await self.search(
            {"type": "collection", "sharedBy": str(self._user_id), "sortBy": "recentlyOpened"}
        )
        return data.results

    async def get_currently_studying_collections(self) -> list[SearchCollectionResult]:
        """Get collections from the 'Continue Studying shelf'.

        This includes collections imported by other users.
        """
        data = await self.search(
            {"shelf": "my_lessons", "type": "collection", "sortBy": "recentlyOpened"}
        )
        return data.results

    async def get_collection_from_id(self, course_id: int) -> CollectionV3:
        """Get a CollectionV3 object.

        This only contains an overview of the collection.
        """
        data = await self._request("GET", f"collections/{course_id}")
        return CollectionV3.model_validate(data)

    async def get_collection_from_id_v2(self, course_id: int) -> Any:
        """Get a raw JSON for a collection (v2 API).

        TODO: make a model for it.
        """
        return await self._request("GET", f"collections/{course_id}", version=2)

    async def get_collection_object_from_id(self, course_id: int) -> Collection | None:
        """Get a custom Collection object from a course_id.

        Used for markdown generation.
        """
        collection = await self.get_collection_from_id_v2(course_id)
        if not collection:
            return None
        if collection.get("detail", "") == "Not found.":
            logger.warning(f"Ghost course at: {get_editor_url(self.lang, course_id, 'course')}")
            return None
        col = Collection()
        col.add_data(self.lang, collection)
        return col

    async def get_audio_from_lesson(self, lesson: LessonV3) -> bytes | None:
        """Get the audio from a lesson. Return None if there is no audio.

        Note: The key with the audio url is 'audio' in V2 and 'audioUrl' in V3.
        """
        if not lesson.audio_url:
            return None
        async with self.session.get(str(lesson.audio_url)) as response:
            return await response.read()

    async def get_stats(self) -> Any:
        """Get reading stats for the last 7 days.

        Period options can be found at (replace lang if needed):
        https://www.lingq.com/api/v3/ja/progress/
        """
        return await self._request(
            method="GET",
            endpoint="progress/chart_data/?metric=reading&period=last_7d",
        )

    """Patch requests"""

    async def patch_audio(self, lesson_id: int, audio: BufferedReader) -> ClientResponse:
        """PATCH. Replace the audio of a lesson."""
        return await self._request(
            "PATCH", f"lessons/{lesson_id}/", data={"audio": audio}, raw=True
        )

    async def patch_text(self, lesson_id: int, text_data: str) -> Any:
        """POST. Replace the text of a lesson.

        Note that this is actually a POST request that works like a patch one.
        """
        return await self._request(
            "POST", f"lessons/{lesson_id}/resplit/", data={"text": text_data}
        )

    async def patch_position(self, lesson_id: int, new_position: int) -> Any:
        """PATCH. Replace the position of a lesson in its course."""
        return await self._request("PATCH", f"lessons/{lesson_id}", data={"pos": new_position})

    async def patch_course(self, lesson_id: int, new_course_id: int) -> Any:
        """PATCH. Move a lesson to another course."""
        return await self._request(
            "PATCH", f"lessons/{lesson_id}", data={"collection": new_course_id}
        )

    async def generate_timestamps(self, lesson_id: int) -> Any:
        """POST. Add timestamps to a lesson."""
        return await self._request("POST", f"lessons/{lesson_id}/genaudio/")

    async def _create_course(self, data: dict[str, Any]) -> Any:
        """POST. Create a course."""
        return await self._request("POST", "collections/", data=data)

    async def create_course(self, title: str, description: str = "") -> Any:
        """Create an empty course given its title and (optional) description.

        Returns the response JSON, which contains an entry "id" for the course id.
        This id can be used for further uploading through post methods.
        """
        return await self._create_course({"title": title, "description": description})

    async def post_from_multipart(self, data: FormData, *, raw: bool = False) -> Any:
        return await self._request("POST", "lessons/import/", data=data, raw=raw)

    async def post_from_data_dict(self, data: dict[str, Any], *, raw: bool = False) -> Any:
        """POST. Post a lesson from a dictionary.

        F.e.
            data = {
                "title": "tmp_title",
                "text": "Hello, world!",
                "status": "private",  # default
                "level": 0,           # default
                "collection": course_id,
                "save": True,         # Needed
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

    async def replace(self, lesson_id: int, replacements: dict[str, str]) -> ClientResponse:
        """POST. Regex-like replace text in a lesson.

        A replacement is a pair {regex: substition}. F.e. {"a": "b", "c": "d"}
        I'm aware that the first argument is a regex because of the error messages
        with the '[]' characters, but I haven't actually used it with a regex.

        This does not use _post because it requires the data to be sent as json.
        """
        return await self._request(
            "POST",
            f"lessons/{lesson_id}/sentences/",
            json={"action": "replace", "text": replacements},
            raw=True,
        )

    async def replace_sentence(self, lesson_id: int, text: str, index: int) -> ClientResponse:
        """POST. Replace a sentence in a lesson."""
        return await self._request(
            "POST",
            f"lessons/{lesson_id}/sentences/",
            json={"action": "update", "index": index, "text": text},
            raw=True,
        )

    async def replace_title(self, lesson_id: int, text: str) -> ClientResponse:
        """POST. Replace the title of a lesson."""
        return await self.replace_sentence(lesson_id, text, index=1)

    async def resplit_lesson(self, lesson_id: int, method: str) -> ClientResponse:
        """Resplit a Japanese lesson using the new splitting logic.

        https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754/5
        """
        if method != "ichimoe":
            msg = "Only method=ichimoe is supported."
            raise NotImplementedError(msg)
        return await self._request(
            "POST",
            f"lessons/{lesson_id}/resplit/",
            data={"method": method},
            raw=True,
        )

    async def delete_course(self, course_id: int) -> None:
        """Delete a course.

        Crashes if the course is not succesfully deleted.
        """
        url = f"{LingqHandler.API_URL_V3}/{self.lang}/collections/{course_id}"
        async with self.session.delete(url, headers=self.config.headers) as response:
            if response.status != 202:
                msg = "The course could not be successfully deleted"
                raise RuntimeError(msg)
