import asyncio
from dataclasses import dataclass
from pathlib import Path

from lingqhandler import LingqHandler
from models.lesson import SimpleLesson


@dataclass
class Token:
    text: str
    timestamp: tuple[float, float] | tuple[None, None]


def sanitize_title(title: str) -> str:
    return title.replace("/", "-")


def format_timestamp(seconds: float) -> str:
    """Format seconds to VTT format: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds * 1000) % 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def to_vtt(ptokens: list[list[Token]]) -> str | None:
    vtt_lines = ["WEBVTT\n"]

    idx_token = 0
    for tokens in ptokens:
        for token in tokens:
            start_time, end_time = token.timestamp
            if start_time is None or end_time is None:
                # Early exit: the text has no timestamps
                return None
            start = format_timestamp(start_time)
            end = format_timestamp(end_time)

            idx_token += 1
            vtt_lines.append(f"{idx_token}")
            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(token.text)
            vtt_lines.append("")

    return "\n".join(vtt_lines)


async def get_lesson_async(
    handler: LingqHandler,
    lesson_id: int,
    download_audio: bool,
    download_timestamps: bool,
    verbose: bool,
) -> SimpleLesson:
    # async with handler:

    # print("HERE")
    lesson = await handler.get_lesson_from_id(lesson_id)
    # print(lesson)
    # print("PAST")

    # The first element is the lesson title, that we don't use
    _, *tokenized_text = lesson.tokenized_text
    paragraph_tokens: list[list[Token]] = []
    for paragraph_data in tokenized_text:
        tokens: list[Token] = []
        for sentence in paragraph_data:
            tokens.append(Token(sentence.text, sentence.timestamp))  # type: ignore
        paragraph_tokens.append(tokens)

    text = lesson.get_raw_text()

    if download_audio:
        audio = await handler.get_audio_from_lesson(lesson)
    else:
        audio = None

    if download_timestamps:
        timestamps = to_vtt(paragraph_tokens)
    else:
        timestamps = None

    simple_lesson = SimpleLesson(
        title=lesson.title,
        collection_title=lesson.collection_title,
        url=str(lesson.url),
        id_=lesson_id,
        text=text,
        audio=audio,
        timestamps=timestamps,
    )

    if verbose:
        print(f"Downloaded lesson: {simple_lesson.title}")

    # print("RETURNING")

    return simple_lesson


def write_lesson(lang: str, lesson: SimpleLesson, opath: Path) -> None:
    collection_title = sanitize_title(lesson.collection_title)
    title = sanitize_title(lesson.title)

    texts_folder = opath / lang / collection_title / "texts"
    audios_folder = opath / lang / collection_title / "audios"
    timestamps_folder = opath / lang / collection_title / "timestamps"

    # Write text
    Path.mkdir(texts_folder, parents=True, exist_ok=True)
    text_path = texts_folder / f"{title}.txt"
    with text_path.open("w", encoding="utf-8") as text_file:
        text_file.write(f"{lesson.title}\n")
        text_file.write(lesson.text)

    # Write audio if any
    if lesson.audio:
        Path.mkdir(audios_folder, parents=True, exist_ok=True)
        mp3_path = audios_folder / f"{title}.mp3"
        with mp3_path.open("wb") as audio_file:
            audio_file.write(lesson.audio)

    # Write timestamps if any
    if lesson.timestamps:
        Path.mkdir(timestamps_folder, parents=True, exist_ok=True)
        vtt_path = timestamps_folder / f"{title}.vtt"
        with vtt_path.open("w", encoding="utf-8") as vtt_file:
            vtt_file.write(lesson.timestamps)


if __name__ == "__main__":
    # Test getting a single lesson
    async def get_lesson_async_tmp(
        lang: str,
        lesson_id: int,
        download_audio: bool,
        download_timestamps: bool,
        verbose: bool,
    ) -> SimpleLesson:
        async with LingqHandler(lang) as handler:
            return await get_lesson_async(
                handler, lesson_id, download_audio, download_timestamps, verbose
            )

    lesson = asyncio.run(
        get_lesson_async_tmp(
            lang="el",
            lesson_id=5897069,
            download_audio=True,
            download_timestamps=True,
            verbose=True,
        )
    )
    write_lesson(
        lang="el",
        lesson=lesson,
        opath=Path("downloads"),
    )
