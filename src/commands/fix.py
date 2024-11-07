import asyncio
from pathlib import Path

from commands.get_lessons import get_lessons_async
from fix_utils.el.fix_greek import fix_latin_letters
from fix_utils.ja.fix_japanese import fix_youtube_newlines
from lingqhandler import LingqHandler


def transformation_fn(lang: str, text: str) -> str:
    # Replace this with your custom logic per language
    match lang:
        case "el":
            print("Fixing latin letters for greek")
            return fix_latin_letters(text)
        case "ja":
            print("Fixing youtube newlines for japanese")
            return fix_youtube_newlines(text)
        case _:
            raise NotImplementedError()


async def fix_async(lang: str, course_id: int) -> None:
    lessons = await get_lessons_async(
        lang,
        course_id,
        skip_downloaded=False,
        download_audio=False,
        download_timestamps=False,
        opath=Path(),
        write=False,
        verbose=False,
    )
    for lesson in lessons:
        text = transformation_fn(lang, lesson.text)
        async with LingqHandler(lang) as handler:
            await handler.patch_text(lesson.id_, text)


def fix(lang: str, course_id: int) -> None:
    asyncio.run(fix_async(lang, course_id))


if __name__ == "__main__":
    fix(lang="el", course_id=1070313)
