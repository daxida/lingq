import asyncio
import os

from lingqhandler import LingqHandler
from utils import double_check, read_sorted_folders, timing  # type: ignore


async def _patch_audios(
    language_code: str, course_id: str, audios_folder: str, from_lesson: int, to_lesson: int
) -> None:
    async with LingqHandler(language_code) as handler:
        collection = await handler.get_collection_json_from_id(course_id)
        assert collection is not None

        lesson_jsons = collection["lessons"][from_lesson - 1 : to_lesson]
        double_check(
            f"Patching audio for course: {collection['title']} ({language_code}) (lessons {from_lesson} to {len(lesson_jsons)})"
        )

        urls = [lesson_json["url"] for lesson_json in lesson_jsons]
        lessons = await handler.get_lessons_from_urls(urls)

        audios_path = read_sorted_folders(audios_folder, mode="human")

        # Patch everything with the same audio in case of a single audio path.
        if len(audios_path) == 1:
            audios_path = [audios_path[0]] * len(lessons)

        print("Confirm the following audio patching:")
        for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
            print(f"  {audio_path} -> {lesson['title']}")
        double_check()

        for idx, (audio_path, lesson) in enumerate(zip(audios_path, lessons), 1):
            audio_path = os.path.join(audios_folder, audio_path)
            audio_files = {"audio": open(audio_path, "rb")}
            await handler.patch(lesson, audio_files)
            print(f"[{idx}/{len(lessons)}] Patched audio for: {lesson['title']}")


@timing
def patch_audios(
    language_code: str, course_id: str, audios_folder: str, from_lesson: int, to_lesson: int
) -> None:
    # This deals with overwriting of existing lessons / collections.
    # The main usecase is to add audio to an already uploaded book where some
    # editing has already be done, and we wouldn't want to upload the text again.

    # The blank audios were found here: https://github.com/anars/blank-audio.
    asyncio.run(_patch_audios(language_code, course_id, audios_folder, from_lesson, to_lesson))


if __name__ == "__main__":
    # Defaults for manually running this script.
    patch_audios(
        language_code="ja",
        course_id="537808",
        audios_folder="src/audios",
        from_lesson=1,
        to_lesson=99,
    )
