import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime as dt
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

# fmt: off
TOEUROPEAN = {
    'Advanced 2'     : 'C2',
    'Advanced 1'     : 'C1',
    'Intermediate 2' : 'B2',
    'Intermediate 1' : 'B1',
    'Beginner 2'     : 'A2',
    'Beginner 1'     : 'A1'
}
# fmt: on


class Config:
    API_URL_V2 = "https://www.lingq.com/api/v2/"
    API_URL_V3 = "https://www.lingq.com/api/v3/"

    def __init__(self):
        # Assumes the scripts are run in the src folder
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

    def get_language_codes(self) -> List:
        """Returns a list of language codes with known words"""
        url = f"{LingqHandler.API_URL_V2}languages"
        response = requests.get(url=url, headers=self.config.headers)
        languages = response.json()
        codes = [lan["code"] for lan in languages if lan["knownWords"] > 0]

        return codes

    def get_all_collections(self, language_code: str) -> Any:
        """
        Return a json file with all the collections in this language.
        """
        url = f"{LingqHandler.API_URL_V3}{language_code}/collections/my/"
        response = requests.get(url=url, headers=self.config.headers)
        my_collections = response.json()

        return my_collections["results"]

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

    def iter_lessons_from_collection(self, collection: Dict, fr_lesson: int, to_lesson: int):
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

    def get_audio_from_lesson(self, lesson: Dict) -> bytes | None:
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
        url = f"{Config.API_URL_V3}{language_code}/lessons/import/"
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


# NOTE: not used
@dataclass
class Lesson:
    title: str = None
    language_code: str = None
    course_url: str = None
    level: str = None
    hasAudio: bool = False
    isShared: bool = False
    update: str = None

    def addData(self, lesson):
        # fmt: off
        self.title      = lesson['collectionTitle']
        self.course_url = f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{lesson['collectionId']}"
        self.level      = TOEUROPEAN.get(lesson['level'], lesson['level'])
        self.hasAudio   = lesson['audio'] is not None
        self.isShared   = lesson['sharedDate'] is not None
        self.update     = lesson['pubDate']
        # fmt: on


@dataclass
class Collection:
    # fmt: off
    _id:            int = 0
    title:          str = None
    language_code:  str = None
    course_url:     str = None
    level:          str = "-"
    hasAudio:       bool = False
    is_shared:      bool = False
    first_update:   str = None
    last_update:    str = None
    amount_lessons: int = 0
    viewsCount:     int = 0
    # fmt: off

    def add_data(self, collection):
        # fmt: off
        self._id          = collection['pk']  # it's pk in V2 and id in V3
        self.title        = collection['title']
        self.course_url   = f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{self._id}"
        # fmt: off

        lessons = collection["lessons"]
        if not lessons:
            print(f"  No lessons found for {self.title}")
            print("  Course url:", self.course_url)
            print("  Api url   :", collection['url'])
            print("  Skipping add_data.")
            return

        # fmt: on
        self.level = TOEUROPEAN.get(collection["level"], collection["level"]) or "-"
        self.hasAudio = lessons[0]["audio"] is not None
        self.last_update = lessons[0]["pubDate"]
        self.first_update = lessons[0]["pubDate"]
        # fmt: on

        for lesson in lessons:
            # The collection has audio if at least one lesson has audio:
            self.hasAudio = self.hasAudio or (lesson["audio"] is not None)

            # The collection is shated if at least one lesson is shared:
            # NOTE: D for private, P for public
            self.is_shared = self.is_shared or (lesson["status"] == "P")
            # print(lesson["status"] == "P")

            # Track the first and last updates:
            cur_update = dt.strptime(lesson["pubDate"], "%Y-%m-%d")
            if dt.strptime(self.first_update, "%Y-%m-%d") > cur_update:
                self.first_update = lesson["pubDate"]
            if dt.strptime(self.last_update, "%Y-%m-%d") < cur_update:
                self.last_update = lesson["pubDate"]

            # The view count is the total sum of the viewsCount of the lessons
            self.viewsCount += lesson["viewsCount"]

        # We remove our own view from the count (assuming we read everything).
        self.amount_lessons = len(lessons)
        self.viewsCount -= self.amount_lessons


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"{CYAN}({f.__name__} {te-ts:2.2f}sec){RESET}")
        return result

    return wrap
