import asyncio
from pathlib import Path

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.utils import double_check, sorted_subpaths, timing


async def patch_audios_async(lang: str, course_id: int, audios_folder: Path) -> None:
    audios_path = sorted_subpaths(audios_folder, mode="human")
    logger.info(f"Found {len(audios_path)} audio(s) at path")

    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return

        collection_title = lessons[0].collection_title
        logger.info(f"Patching audio for course: {collection_title} ({lang})")

        if len(audios_path) == 1 and len(lessons) > 1:
            logger.info("Patching all the lessons with the same audio")
            audios_path = [audios_path[0]] * len(lessons)

        for idx, (apath, lesson) in enumerate(zip(audios_path, lessons), 1):
            print(f"  {apath} -> {lesson.title}")
        double_check("Confirm the previous audio patching:")

        for idx, (apath, lesson) in enumerate(zip(audios_path, lessons), 1):
            audio = apath.open("rb")
            await handler.patch_audio(lesson.id, audio)
            logger.success(f"[{idx}/{len(lessons)}] Patched audio for: {lesson.title}")


@timing
def patch_audios(lang: str, course_id: int, audios_folder: Path) -> None:
    """Deals with overwriting of existing lessons / collections.
    The main usecase is to add audio to an already uploaded book where some
    editing has already be done, and we wouldn't want to upload the text again.
    """
    # The blank audios were found here: https://github.com/anars/blank-audio.
    asyncio.run(patch_audios_async(lang, course_id, audios_folder))


if __name__ == "__main__":
    # Defaults for manually running this script.
    patch_audios(
        lang="ja",
        course_id=537808,
        audios_folder=Path("example/audios"),
    )
