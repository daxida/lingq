import asyncio
from pathlib import Path

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.models.lesson_v3 import LessonV3
from lingq.utils import timing


def sanitize_title(title: str) -> str:
    return title.replace("/", "-")


async def get_lesson_async(
    handler: LingqHandler,
    lesson_id: int,
    download_audio: bool,
    download_timestamps: bool,
) -> LessonV3 | None:
    lesson = await handler.get_lesson_from_id(lesson_id)
    if lesson is None:
        return None

    if download_audio:
        audio = await handler.get_audio_from_lesson(lesson)
        lesson._downloaded_audio = audio

    if download_timestamps:
        timestamps = lesson.to_vtt()
        lesson._timestamps = timestamps

    return lesson


def write_lesson(lang: str, lesson: LessonV3, opath: Path, idx: int | None) -> None:
    collection_title = sanitize_title(lesson.collection_title)
    title = sanitize_title(lesson.title)

    if idx:
        title = f"{idx:02d}. {title}"

    texts_folder = opath / lang / collection_title / "texts"
    audios_folder = opath / lang / collection_title / "audios"
    timestamps_folder = opath / lang / collection_title / "timestamps"

    # Write text
    Path.mkdir(texts_folder, parents=True, exist_ok=True)
    text_path = texts_folder / f"{title}.txt"
    with text_path.open("w", encoding="utf-8") as text_file:
        # Cf. https://forum.lingq.com/t/bug-lesson-titles/1323451
        # text_file.write(f"{lesson.title}\n")
        text_file.write(lesson.get_raw_text())

    # Write audio if any
    if audio := lesson._downloaded_audio:
        Path.mkdir(audios_folder, parents=True, exist_ok=True)
        mp3_path = audios_folder / f"{title}.mp3"
        with mp3_path.open("wb") as audio_file:
            audio_file.write(audio)

    # Write timestamps if any
    if timestamps := lesson._timestamps:
        Path.mkdir(timestamps_folder, parents=True, exist_ok=True)
        vtt_path = timestamps_folder / f"{title}.vtt"
        with vtt_path.open("w", encoding="utf-8") as vtt_file:
            vtt_file.write(timestamps)


async def _get_lesson_async(
    lang: str,
    lesson_id: int,
    download_audio: bool,
    download_timestamps: bool,
) -> LessonV3 | None:
    """Same as get_lesson_async but does not expect a handler."""
    async with LingqHandler(lang) as handler:
        return await get_lesson_async(
            handler,
            lesson_id,
            download_audio,
            download_timestamps,
        )


@timing
def get_lesson(
    lang: str,
    lesson_id: int,
    opath: Path,
    *,
    download_audio: bool,
    download_timestamps: bool,
) -> None:
    """Get a lesson from a lesson id.

    Download text and/or audio from a lesson given the language code and the lesson ID.
    """
    lesson = asyncio.run(
        _get_lesson_async(
            lang=lang,
            lesson_id=lesson_id,
            download_audio=download_audio,
            download_timestamps=download_timestamps,
        )
    )
    if lesson:
        write_lesson(
            lang=lang,
            lesson=lesson,
            opath=opath,
            idx=None,
        )
        logger.success(f"'{lesson.title}'")


if __name__ == "__main__":
    # Test getting a single lesson
    get_lesson(
        lang="el",
        lesson_id=5897069,
        download_audio=True,
        download_timestamps=True,
        opath=Path("downloads"),
    )
