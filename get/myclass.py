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
    updated: str = None

    def addData(self, lesson):
        # fmt: off
        self.title      = lesson['collectionTitle']
        self.course_url = f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{lesson['collectionId']}"
        self.level      = TOEUROPEAN.get(lesson['level'], lesson['level'])
        self.hasAudio   = lesson['audio'] is not None
        self.isShared   = lesson['sharedDate'] is not None
        self.updated    = lesson['pubDate']
        # fmt: on


@dataclass
class Collection:
    # fmt: off
    title:         str = None
    language_code: str = None
    course_url:    str = None
    level:         str = None
    hasAudio:      bool = False
    isShared:      bool = False
    updated:       str = None
    viewsCount:    int = 0
    # fmt: on

    def add_data(self, collection):
        if not collection["lessons"]:
            print(f"No lessons found: skipping add_data.")
            return

        # fmt: off
        self.title      = collection['title']
        self.course_url = f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{collection['pk']}"
        self.level      = TOEUROPEAN.get(collection['level'], collection['level'])

        self.hasAudio   = collection['lessons'][0]['audio'] is not None
        self.isShared   = collection['lessons'][0]['sharedDate'] is not None
        self.updated    = collection['lessons'][0]['pubDate']
        # fmt: on

        for lesson in collection["lessons"]:
            # The collection has audio if at least one lesson has audio:
            self.hasAudio = self.hasAudio or (lesson["audio"] is not None)
            # The collection is shared if at least one lesson is shared:
            self.isShared = self.isShared or (lesson["sharedDate"] is not None)
            # The collection update is the latest update:
            if dt.strptime(self.updated, "%Y-%m-%d") < dt.strptime(lesson["pubDate"], "%Y-%m-%d"):
                self.update = lesson["pubDate"]
            # The view count is the total sum of the viewsCount of the lessons
            self.viewsCount += lesson["viewsCount"]

        # We remove our own view from the count (assuming we read everything).
        lessons_amount = len(collection["lessons"])
        self.viewsCount -= lessons_amount
