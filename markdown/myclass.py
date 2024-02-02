from dataclasses import dataclass
from datetime import datetime as dt

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
    _id: int = 0
    title: str = None
    language_code: str = None
    course_url: str = None
    level: str = "-"
    hasAudio: bool = False
    status: str = None
    first_update: str = None
    last_update: str = None
    amount_lessons: int = 0
    viewsCount: int = 0

    def addData(self, collection):
        lessons = collection["lessons"]

        # fmt: off
        self._id          = collection['pk']  # it's pk in V2 and id in V3
        self.title        = collection['title']
        self.course_url   = f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{self._id}"
        self.level        = TOEUROPEAN.get(collection['level'], collection['level']) or '-'
        self.hasAudio     = lessons[0]['audio'] is not None
        self.last_update  = lessons[0]['pubDate']
        self.first_update = lessons[0]['pubDate']
        # fmt: on

        for lesson in lessons:
            # The collection has audio if at least one lesson has audio:
            self.hasAudio = self.hasAudio or (lesson["audio"] is not None)

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
