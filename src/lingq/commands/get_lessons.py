import asyncio
from pathlib import Path

from lingq.commands.get_lesson import get_lesson_async, sanitize_title, write_lesson
from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.collection_v3 import CollectionLessonResult
from lingq.models.lesson_v3 import LessonV3
from lingq.utils import get_editor_url, timing


def filter_downloaded(
    texts_path: Path, lessons: list[CollectionLessonResult]
) -> list[CollectionLessonResult]:
    if not texts_path.exists():
        return lessons

    collection_title = lessons[0].collection_title
    text_files = [path.name for path in texts_path.iterdir()]
    logger.trace(text_files)
    filtered_lessons = [
        lesson for lesson in lessons if f"{sanitize_title(lesson.title)}.txt" not in text_files
    ]
    n_skipped = len(lessons) - len(filtered_lessons)
    logger.info(f"'{collection_title}' Skipped {n_skipped} out of {len(lessons)} lessons.")
    return filtered_lessons


async def get_lessons_async(
    lang: str,
    course_id: int,
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    write: bool,
    with_index: bool,
) -> list[LessonV3]:
    async with LingqHandler(lang) as handler:
        lessons = await handler.get_collection_lessons_from_id(course_id)
        if not lessons:
            return []

        editor_url = get_editor_url(lang, course_id, "course")
        logger.trace(editor_url)
        collection_title = lessons[0].collection_title

        if skip_downloaded:
            texts_folder = opath / lang / collection_title / "texts"
            lessons = filter_downloaded(texts_folder, lessons)
            if not lessons:
                return []

        tasks = [
            get_lesson_async(
                handler,
                lesson_json.id,
                download_audio,
                download_timestamps,
            )
            for lesson_json in lessons
        ]
        lessons = await asyncio.gather(*tasks)
        lessons = [les for les in lessons if les is not None]
        logger.success(f"'{collection_title}'")

        if write:
            for _idx, lesson in enumerate(lessons, 1):
                idx = _idx if with_index else None
                write_lesson(lang, lesson, opath, idx)

        return lessons


@timing
def get_lessons(
    lang: str,
    course_id: int,
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    write: bool,
    with_index: bool,
) -> None:
    """Get all lessons from a course id.

    Download text and/or audio from a course given the language code and the course ID.

    Args:
        lang (str): The language code of the course.
        course_id (str): The ID of the course. This is the last number in the course URL.
        opath (Path): Path to the folder where the downloaded text and audio files will be saved.

        download_audio (bool): If True, downloads the audio files for the lessons.
        download_timestamps (bool): If True, downloads the timestamps files for the lessons.
        skip_downloaded (bool): If True, skip downloading already downloaded lessons.

        TODO: Update me

    Creates a 'download' folder and saves the text/audio in 'text'/'audio' subfolders.
    """
    asyncio.run(
        get_lessons_async(
            lang,
            course_id,
            opath,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
            skip_downloaded=skip_downloaded,
            write=write,
            with_index=with_index,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    get_lessons(
        lang="el",
        course_id=730129,
        opath=Path("downloads"),
        download_audio=True,
        download_timestamps=True,
        skip_downloaded=False,
        write=True,
        with_index=False,
    )
