import os
import time
from functools import wraps
from dotenv import dotenv_values
from dataclasses import dataclass
from datetime import datetime as dt

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
