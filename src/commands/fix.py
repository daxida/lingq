import asyncio
from pathlib import Path

from commands.get_lessons import get_lessons_async
from fix_utils.el.fix_greek import fix_latin_letters
from fix_utils.ja.fix_japanese import fix_youtube_newlines
from lingqhandler import LingqHandler


def transformation_fn(language_code: str, text: str) -> str:
    # Replace this with your custom logic per language
    match language_code:
        case "el":
            print("Fixing latin letters for greek")
            return fix_latin_letters(text)
        case "ja":
            print("Fixing youtube newlines for japanese")
            return fix_youtube_newlines(text)
        case _:
            raise NotImplementedError()


async def fix_async(language_code: str, course_id: int) -> None:
    lessons = await get_lessons_async(
        language_code,
        course_id,
        skip_downloaded=False,
        download_audio=False,
        download_timestamps=False,
        opath=Path(),
        write=False,
        verbose=False,
    )
    for lesson in lessons:
        text = transformation_fn(language_code, lesson.text)
        async with LingqHandler(language_code) as handler:
            await handler.patch_text(lesson.id_, text)


def fix(language_code: str, course_id: int) -> None:
    asyncio.run(fix_async(language_code, course_id))


if __name__ == "__main__":
    fix(language_code="el", course_id=1070313)
