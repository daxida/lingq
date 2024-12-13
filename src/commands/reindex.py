import asyncio
import re

from lingqhandler import LingqHandler
from log import logger


async def reindex_async(lang: str, course_id: int) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return

        padding = len(str(len(lessons)))
        for idx, lesson in enumerate(lessons, 1):
            # Remove initial numbers if any.
            # Ex. "1.2.1   Title" => " Title")
            new_title = re.sub(r"^((\d+\.)*\d+.?)\s+", " ", lesson.title)
            await handler.replace_title(lesson.id, f"{idx:0{padding}d}. {new_title}")
        logger.success(f"Reindexed course {lessons[0].collection_title}")


def reindex(lang: str, course_id: int) -> None:
    """Reindex titles in a course."""
    asyncio.run(reindex_async(lang, course_id))


if __name__ == "__main__":
    reindex(lang="ja", course_id=537808)
