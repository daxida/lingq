import asyncio
import re

from lingq.lingqhandler import LingqHandler
from lingq.log import logger


def remove_leading_numbers(text: str) -> str:
    # Remove initial numbers if any.
    # Ex. "1.2.1   Title" => " Title")
    text = re.sub(r"^((\d+\.)*\d+.?)\s*", " ", text)
    return text


def replace_title(title: str, idx: int, padding: int) -> str:
    clean_title = remove_leading_numbers(title)
    new_title = f"{idx:0{padding}d}.{clean_title}"
    return new_title


async def reindex_async(lang: str, course_id: int, *, dry_run: bool) -> None:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return

        padding = len(str(len(lessons)))

        if dry_run:
            msg_parts: list[str] = []
            # re-enables bold to not mess with logger formatting
            arrow = "\x1b[32m➜\x1b[0m\x1b[1m"
            for idx, lesson in enumerate(lessons, 1):
                new_title = replace_title(lesson.title, idx, padding)
                msg_line = f"{lesson.title} {arrow} {new_title}"
                msg_parts.append(msg_line)
            msg = "\n".join(msg_parts)
            logger.info(f"Reindexing would change:\n{msg}")
            return

        for idx, lesson in enumerate(lessons, 1):
            new_title = replace_title(lesson.title, idx, padding)
            await handler.replace_title(lesson.id, new_title)
        logger.success(f"Reindexed course {lessons[0].collection_title}")


def reindex(lang: str, course_id: int, *, dry_run: bool = False) -> None:
    """Reindex course titles."""
    asyncio.run(reindex_async(lang, course_id, dry_run=dry_run))


if __name__ == "__main__":
    reindex(lang="ja", course_id=537808)
