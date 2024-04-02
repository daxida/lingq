import json
import os
import sys
import time
from functools import wraps
from typing import Any, Dict, List

import requests
from dotenv import dotenv_values
from requests import Response
from requests_toolbelt.multipart.encoder import MultipartEncoder

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

    def __init__(self):
        self.config = Config()

    def get_language_codes(self) -> List[str]:
        """Returns a list of language codes with known words"""
        url = f"{LingqHandler.API_URL_V2}languages"
        response = requests.get(url=url, headers=self.config.headers)
        languages = response.json()
        codes = [lan["code"] for lan in languages if lan["knownWords"] > 0]

        return codes

    def get_my_collections(self, language_code: str) -> Any:
        """
        Return a json file with all my imported collections in this language.
        """
        url = f"{LingqHandler.API_URL_V3}{language_code}/collections/my/"
        response = requests.get(url=url, headers=self.config.headers)
        collections = response.json()

        assert collections["next"] is None, "We are missing some collections"

        return collections["results"]

    def get_currently_studying_collections(self, language_code: str) -> Any:
        """
        Return a json file with all the studied collections (Continue Studying shelf) in this language.
        """
        url = f"{LingqHandler.API_URL_V3}{language_code}/search/?shelf=my_lessons&type=collection&sortBy=recentlyOpened"
        response = requests.get(url=url, headers=self.config.headers)
        collections = response.json()

        assert collections["next"] is None, "We are missing some collections"

        return collections["results"]

    def get_collection_from_id(self, language_code: str, course_id: str) -> Any:
        """Return a json file with collection in this language"""
        url = f"{LingqHandler.API_URL_V2}{language_code}/collections/{course_id}"
        response = requests.get(url=url, headers=self.config.headers)
        collection = response.json()

        if not collection["lessons"]:
            editor_url = f"https://www.lingq.com/learn/{language_code}/web/editor/courses/"
            msg = f"The collection {collection['title']} at {editor_url}{course_id} has no lessons, (delete it?)"
            print(msg)

        return collection

    def iter_lessons_from_collection(self, collection: Any, fr_lesson: int, to_lesson: int):
        """Iterate over the lessons of a given collection between indices fr_lesson to to_lesson"""
        for lesson in collection["lessons"][fr_lesson - 1 : to_lesson]:
            response = requests.get(lesson["url"], headers=self.config.headers)

            if response.status_code != 200:
                print(f"Error in iter_lesson for lesson: {lesson['title']}")
                print(f"Response code: {response.status_code}")
                print(f"Response text: {response.text}")
                break

            lesson_json = response.json()
            yield lesson_json

    def get_lesson_from_url(self, url: str) -> Any:
        """Return a json file with the lesson, given its url."""
        lesson_response = requests.get(url, headers=self.config.headers)
        lesson = lesson_response.json()

        return lesson

    def get_audio_from_lesson(self, lesson: Any) -> bytes | None:
        """
        From a list of lessons obtained by collection["lessons"], gets the audio
        (if any) given a lesson of that list.
        """
        audio = None
        if lesson["audio"]:
            audio_response = requests.get(lesson["audio"])
            audio = audio_response.content

        return audio

    def patch_audio(self, language_code: str, lesson_id: str, audio_files: Dict) -> Response:
        """Returns the response for error management"""
        url = f"{LingqHandler.API_URL_V3}{language_code}/lessons/{lesson_id}/"
        response = requests.patch(url=url, headers=self.config.headers, files=audio_files)

        if response.status_code != 200:
            print(f"Response code: {response.status_code}")
            print(f"Response text: {response.text}")

        return response

    def post_from_multiencoded_data(self, language_code: str, data: MultipartEncoder) -> Response:
        """Returns the response for error management"""
        headers = {**self.config.headers} | {"Content-Type": data.content_type}
        url = f"{LingqHandler.API_URL_V3}{language_code}/lessons/import/"
        response = requests.post(url=url, data=data, headers=headers)

        if response.status_code != 201:
            print(f"Response code: {response.status_code}")
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
