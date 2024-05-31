import asyncio
import os
from os import path
from typing import Any, List

from lingqhandler import LingqHandler
from utils import double_check, read_sorted_folders, timing  # type: ignore

# This deals with overwriting of existing lessons / collections.
# The main usecase is to add audio to an already uploaded book where some
# editing has already be done, and we wouldn't want to upload the text again.

# The blank audios were found here: https://github.com/anars/blank-audio.

LANGUAGE_CODE = "ja"
COURSE_ID = "537808"
AUDIOS_FOLDER = "audios"


async def patch_single_audio(
    handler: LingqHandler, audio_path: str, idx: int, lesson: Any, max_iterations: int
) -> None:
    url = lesson["url"]
    lesson_json = await handler.get_lesson_from_url(url)
    audio_files = {"audio": open(audio_path, "rb")}
    await handler.patch(lesson_json, audio_files)
    print(f"[{idx}/{max_iterations}] Patched audio for: {lesson['title']}")


async def patch_blank_audio(
    handler: LingqHandler, collection: Any, from_lesson: int, to_lesson: int
) -> None:
    msg = f"Patching blank audio for course: {collection['title']} (lessons {from_lesson} to {to_lesson})"
    double_check(msg)

    lessons = collection["lessons"][from_lesson - 1 : to_lesson]
    max_iterations = len(lessons)
    blank_audio_path = os.path.join(AUDIOS_FOLDER, "15-seconds-of-silence.mp3")

    tasks = [
        patch_single_audio(handler, blank_audio_path, idx, lesson, max_iterations)
        for idx, lesson in enumerate(lessons, 1)
    ]
    await asyncio.gather(*tasks)

    print("patch_blank_audio finished!")


async def patch_bulk_audios(
    handler: LingqHandler, collection: Any, audios_path: List[str], from_lesson: int, to_lesson: int
) -> None:
    urls = [lesson["url"] for lesson in collection["lessons"][from_lesson - 1 : to_lesson]]
    lessons = await handler.get_lessons_from_urls(urls)
    max_iterations = min(len(lessons), len(audios_path))

    print("Confirm the following audio patching:")
    for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
        print(f"  {audio_path} -> {lesson['title']}")
    double_check()

    for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
        audio_path = path.join(AUDIOS_FOLDER, audio_path)
        audio_files = {"audio": open(audio_path, "rb")}
        await handler.patch(lesson, audio_files)
        print(f"[{idx}/{max_iterations}] Patched audio for: {lesson['title']}")

    print("patch_bulk_audios finished!")


async def resplit_japanese(
    handler: LingqHandler, collection: Any, from_lesson: int, to_lesson: int
):
    """
    Re-split an existing lesson in japanese with ichimoe.
    Cf: https://forum.lingq.com/t/refining-parsing-in-spaceless-languages-like-japanese-with-ai/179754
    """

    assert handler.language_code == "ja"
    msg = (
        f"Resplitting text for course: {collection['title']} (lessons {from_lesson} to {to_lesson})"
    )
    double_check(msg)

    urls = [lesson["url"] for lesson in collection["lessons"][from_lesson - 1 : to_lesson]]
    lessons = await handler.get_lessons_from_urls(urls)

    for lesson in lessons:
        await handler.resplit_lesson(lesson, method="ichimoe")
        print(f"Resplit text for: {lesson['title']}")


async def patch():
    async with LingqHandler(LANGUAGE_CODE) as handler:
        collection = await handler.get_collection_json_from_id(COURSE_ID)

        # await patch_blank_audio(handler, collection, 1, 3)
        # audios_path = read_sorted_folders(AUDIOS_FOLDER, mode="human")
        # await patch_bulk_audios(handler, collection, audios_path, 1, 5)
        await resplit_japanese(handler, collection, 1, 200)


@timing
def main():
    asyncio.run(patch())


if __name__ == "__main__":
    main()
