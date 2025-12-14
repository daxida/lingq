import asyncio
import sys
from io import BufferedReader
from typing import Any, Self, TypedDict, Unpack

from aiohttp import ClientResponse, ClientSession, FormData
from aiohttp_retry import ExponentialRetry, RetryClient

from lingq.config import Config
from lingq.log import logger
from lingq.models.collection import Collection
from lingq.models.collection_v3 import (
    CollectionLessonResult,
    CollectionLessons,
    CollectionV3,
    SearchCollectionResult,
    SearchCollections,
)
from lingq.models.counter import Counter
from lingq.models.language import Language
from lingq.models.lesson_v3 import LOCKED_REASON_CHOICES, LessonV3
from lingq.models.my_collections import MyCollections
from lingq.utils import get_editor_url, model_validate_or_exit


class RequestKwargs(TypedDict, total=False):
    params: dict[str, Any]
    json: dict[str, Any]
    data: Any


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

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
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
                        logger.error("Invalid API key. Exiting.")
                        sys.exit(1)
                    case _:
                        logger.error("Uncaught detail")
            logger.error(f"[{response.status}] Response JSON:\n{response_json}")
        else:
            logger.error(f"Response text: {response.text}")

    def url(self, endpoint: str, *, version: int, add_language: bool) -> str:
        base_api_url = {
            1: "https://www.lingq.com/api",
            2: "https://www.lingq.com/api/v2",
            3: "https://www.lingq.com/api/v3",
        }[version]

        if add_language:
            return f"{base_api_url}/{self.lang}/{endpoint}"
        return f"{base_api_url}/{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        version: int = 3,
        add_language: bool = True,
        max_retries: int = 4,
        **kwargs: Unpack[RequestKwargs],
    ) -> Any:
        """Generic request.

        On error, retry 'max_retries' times.

        That is, loop until we get a json different from:
        * {'isLocked': 'TOKENIZE_TEXT', 'errorType': 'locked'}
        * {'isLocked': 'GENERATE_TIMESTAMPS', 'errorType': 'locked'}
        * ["Can't execute: Cannot save changes at the moment. Please try again later."]

        Exits in case of failure after 'max_retries' times.
        """

        url = self.url(endpoint, version=version, add_language=add_language)
        logger.trace(f"{method.upper()} {url}")
        if params := kwargs.get("params", ""):
            logger.trace(f"{params=}")

        for retry in range(1, max_retries + 1):
            async with self.session.request(
                method.lower(), url, headers=self.config.headers, **kwargs
            ) as response:
                json = await response.json()

                if 200 <= response.status < 300:
                    return json

                if isinstance(json, dict) and json.get("errorType", "") == "locked":
                    reason = json.get("isLocked", "")
                    if reason not in LOCKED_REASON_CHOICES:
                        logger.warning(f"Unexpected lock reason: {reason}")
                    msg = f"Content is locked at {reason}. Retrying... ({retry}/{max_retries})"
                    logger.debug(msg)
                elif isinstance(json, dict) and json.get("detail", "") == "Not found.":
                    msg = f"{f'{method.upper()} {url}'} was not found."
                    logger.warning(msg)
                    return json
                elif isinstance(json, list) and json[0].startswith(
                    "Can't execute: Cannot save changes at the moment"
                ):
                    msg = f"Can't execute at the moment. Retrying... ({retry}/{max_retries})"
                    logger.debug(msg)
                else:
                    await self.response_debug(response)

                await asyncio.sleep(2**retry)

        msg = f"Could not get content after {max_retries} retries"
        logger.error(msg)
        raise RuntimeError(msg)

    """Get requests"""

    async def get_user_id(self) -> None:
        """Get and cache the user id."""
        if self._user_id is None:
            data = await self._request("GET", "profile/", version=1, add_language=False)
            self._user_id = data["id"]
            logger.trace(f"Cached user id {self._user_id}")

    async def _get_langs(self) -> list[Language]:
        """Get a list of all languages recognized by LingQ.

        https://www.lingq.com/apidocs/api-2.0.html#get (outdated)
        """
        data = await self._request("GET", "languages", version=2, add_language=False)
        return [Language.model_validate(lang) for lang in data]

    async def _get_user_langs(self) -> list[str]:
        """Get a list of language codes with known words."""
        langs = await self._get_langs()
        return [lang.code for lang in langs if lang.known_words > 0]

    @classmethod
    def get_user_langs(cls) -> list[str]:
        """Get a list of language codes with known words.

        This is a class method since it does not require initializing a language code.
        """

        async def tmp() -> list[str]:
            async with cls("Filler") as handler:
                return await handler._get_user_langs()

        return asyncio.run(tmp())

    async def get_lesson_from_id(self, lesson_id: int) -> LessonV3:
        """Get a lesson, from its id.

        Example:
            id: 34754329
            url: https://www.lingq.com/api/v3/LANG/lessons/ID/

        """
        data = await self._request("GET", f"lessons/{lesson_id}/")
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
        base_url = self.url("", version=3, add_language=True)
        base_url_size = len(base_url)
        url = f"{base_url}collections/{course_id}/lessons/"
        collection_lessons: list[CollectionLessonResult] = []
        cur_url = url

        while cur_url:
            endpoint = cur_url[base_url_size:]
            res_json = await self._request("GET", endpoint)
            collection_lessons_at_page = CollectionLessons.model_validate(res_json)
            collection_lessons.extend(collection_lessons_at_page.results)
            cur_url = collection_lessons_at_page.next

        if not collection_lessons:
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

    async def search(self, params: dict[str, Any]) -> list[SearchCollectionResult]:
        data = await self._request("GET", "search", params=params)
        search_collections = SearchCollections.model_validate(data)
        results: list[SearchCollectionResult] = search_collections.results  # convince mypy
        return results

    async def get_my_collections_shared(self) -> list[SearchCollectionResult]:
        await self.get_user_id()
        return await self.search(
            {"type": "collection", "sharedBy": str(self._user_id), "sortBy": "recentlyOpened"}
        )

    async def get_currently_studying_collections(self) -> list[SearchCollectionResult]:
        """Get collections from the 'Continue Studying shelf'.

        This includes collections imported by other users.
        """
        return await self.search(
            {"shelf": "my_lessons", "type": "collection", "sortBy": "recentlyOpened"}
        )

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

    async def patch_audio(self, lesson_id: int, audio: BufferedReader) -> Any:
        """PATCH. Replace the audio of a lesson."""
        return await self._request("PATCH", f"lessons/{lesson_id}/", data={"audio": audio})

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

    async def post_from_multipart(self, data: FormData) -> Any:
        return await self._request("POST", "lessons/import/", data=data)

    async def post_from_data_dict(self, data: dict[str, Any]) -> Any:
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
        return await self.post_from_multipart(fdata)

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

    async def replace(self, lesson_id: int, replacements: dict[str, str]) -> Any:
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
        )

    async def _has_title_paragraph(self, lesson_id: int) -> bool:
        """This is awful and I am convinced it is exactly what LingQ does internally."""
        paragraphs = await self._request("GET", f"lessons/{lesson_id}/paragraphs/")
        has_title = (
            isinstance(paragraphs, list)
            and len(paragraphs) > 0
            and (paragraphs[0].get("style", "") == "h1")
        )
        if not has_title:
            # Issue a warning since you probably always want a title paragraph
            editor_url = get_editor_url(self.lang, lesson_id, "lesson")
            logger.warning(f"Missing title paragraph at lesson @ {editor_url}")
        return has_title

    async def replace_title(self, lesson_id: int, text: str) -> Any:
        """POST/PATCH. Replace the title of a lesson."""
        has_title = await self._has_title_paragraph(lesson_id)
        if has_title:
            # Works if the first line is TITLE
            return await self._request(
                "POST",
                f"lessons/{lesson_id}/sentences/",
                json={"action": "update", "index": 1, "text": text},
            )
        else:
            # Works if the first line is PARAGRAPH 1 (~~no title, f.e. youtube import)
            # Does not modify the first sentence, but then again, there is no guarantee that
            # we _want_ to modify the first sentence, since it may not be the title...
            return await self._request(
                "PATCH",
                f"lessons/{lesson_id}",
                data={"title": text},
            )

    async def resplit_lesson(self, lesson_id: int, data: dict[str, str] = {}) -> Any:
        """POST. Resplit a lesson."""
        if self.lang == "ja":
            # https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754/5
            # As of 2025/12/13 this is still the so-called AI-generated split logic.
            assert len(data) == 0
            return await self._request(
                "POST",
                f"lessons/{lesson_id}/resplit/",
                data={"method": "ichimoe"},
            )
        else:
            # We need to send the Lesson text: {"text": "Raw text.\nNo formatting.\n\nJust chars."}
            assert len(data) > 0
            return await self._request(
                "POST",
                f"lessons/{lesson_id}/resplit/",
                data=data,
            )

    async def delete_course(self, course_id: int) -> None:
        """Delete a course.

        Crashes if the course is not succesfully deleted.
        """
        base_url = self.url("", version=3, add_language=True)
        url = f"{base_url}collections/{course_id}"
        logger.trace(f"DELETE {url}")
        async with self.session.delete(url, headers=self.config.headers) as response:
            if response.status != 202:
                msg = "The course could not be successfully deleted"
                raise RuntimeError(msg)
