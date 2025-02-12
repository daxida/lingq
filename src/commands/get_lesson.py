import asyncio
from pathlib import Path

from lingqhandler import LingqHandler
from models.lesson_v3 import LessonV3


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
        text_file.write(f"{lesson.title}\n")
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


if __name__ == "__main__":
    # Test getting a single lesson
    async def get_lesson_async_tmp(
        lang: str,
        lesson_id: int,
        download_audio: bool,
        download_timestamps: bool,
    ) -> LessonV3 | None:
        async with LingqHandler(lang) as handler:
            return await get_lesson_async(handler, lesson_id, download_audio, download_timestamps)

    lesson = asyncio.run(
        get_lesson_async_tmp(
            lang="el",
            lesson_id=5897069,
            download_audio=True,
            download_timestamps=True,
        )
    )
    if lesson:
        write_lesson(
            lang="el",
            lesson=lesson,
            opath=Path("downloads"),
            idx=None,
        )
