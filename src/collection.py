from dataclasses import dataclass
from datetime import datetime as dt
from typing import Any

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
class Collection:
    # fmt: off
    _id:            int = 0
    title:          str | None = None
    language_code:  str | None = None
    course_url:     str | None = None
    level:          str = "-"
    hasAudio:       bool = False
    is_shared:      bool = False
    first_update:   str | None = None
    last_update:    str | None = None
    amount_lessons: int = 0
    viewsCount:     int = 0
    # fmt: on

    def add_data(self, collection: Any) -> None:
        """Transfer the data from the JSON to the Collection object"""

        self._id = collection["pk"]  # it's pk in V2 and id in V3
        self.title = collection["title"]
        self.course_url = (
            f"https://www.lingq.com/en/learn/{self.language_code}/web/library/course/{self._id}"
        )

        lessons = collection["lessons"]
        if not lessons:
            print(f"  No lessons found for {self.title}")
            print("  Course url:", self.course_url)
            print("  Api url   :", collection["url"])
            print("  Skipping add_data.")
            return

        self.level = TOEUROPEAN.get(collection["level"], collection["level"]) or "-"
        self.hasAudio = lessons[0]["audio"] is not None
        self.last_update = lessons[0]["pubDate"]
        self.first_update = lessons[0]["pubDate"]

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
