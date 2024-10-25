import asyncio
from dataclasses import dataclass
from pathlib import Path

from lingqhandler import LingqHandler
from models.lesson import Lesson


@dataclass
class Token:
    text: str
    timestamp: tuple[float, float]


def sanitize_title(title: str) -> str:
    return title.replace("/", "-")


def get_raw_text(ptokens: list[list[Token]]) -> str:
    return "\n".join(
        " ".join(token.text for token in sentence_tokens) for sentence_tokens in ptokens
    )


def format_timestamp(seconds: float) -> str:
    """Format seconds to VTT format: HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds * 1000) % 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def get_vtt_timestamps(ptokens: list[list[Token]]) -> str:
    vtt_lines = ["WEBVTT\n"]

    for tokens in ptokens:
        for i, token in enumerate(tokens, 1):
            start_time, end_time = token.timestamp
            start = format_timestamp(start_time)
            end = format_timestamp(end_time)

            vtt_lines.append(f"{i}")
            vtt_lines.append(f"{start} --> {end}")
            vtt_lines.append(token.text)
            vtt_lines.append("")

    return "\n".join(vtt_lines)


async def get_lesson_async(
    handler: LingqHandler,
    lesson_id: str,
    download_audio: bool,
    download_timestamps: bool,
    verbose: bool,
) -> Lesson:
    lesson_json = await handler.get_lesson_from_id(lesson_id)

    # The first element is the lesson title, that we don't use
    _, *tokenized_text = lesson_json["tokenizedText"]
    paragraph_tokens: list[list[Token]] = []
    for paragraph_data in tokenized_text:
        tokens: list[Token] = []
        for sentence in paragraph_data:
            tokens.append(Token(sentence["text"], sentence["timestamp"]))
        paragraph_tokens.append(tokens)

    text = get_raw_text(paragraph_tokens)

    if download_audio:
        audio = await handler.get_audio_from_lesson(lesson_json)
    else:
        audio = None

    if download_timestamps:
        # TODO: Better error handling
        try:
            timestamps = get_vtt_timestamps(paragraph_tokens)
        except:
            timestamps = None
    else:
        timestamps = None

    lesson = Lesson(
        title=sanitize_title(lesson_json["title"]),
        collection_title=sanitize_title(lesson_json["collectionTitle"]),
        url=lesson_json["url"],
        id_=lesson_id,
        text=text,
        audio=audio,
        timestamps=timestamps,
    )

    if verbose:
        print(f"Downloaded lesson: {lesson.title}")

    return lesson


def write_lesson(language_code: str, lesson: Lesson, opath: Path) -> None:
    texts_folder = opath / language_code / lesson.collection_title / "texts"
    audios_folder = opath / language_code / lesson.collection_title / "audios"
    timestamps_folder = opath / language_code / lesson.collection_title / "timestamps"

    # Write text
    Path.mkdir(texts_folder, parents=True, exist_ok=True)
    text_path = texts_folder / f"{lesson.title}.txt"
    with text_path.open("w", encoding="utf-8") as text_file:
        text_file.write(f"{lesson.title}\n")
        text_file.write(lesson.text)

    # Write audio if any
    if lesson.audio:
        Path.mkdir(audios_folder, parents=True, exist_ok=True)
        mp3_path = audios_folder / f"{lesson.title}.mp3"
        with mp3_path.open("wb") as audio_file:
            audio_file.write(lesson.audio)

    # Write timestamps if any
    if lesson.timestamps:
        Path.mkdir(timestamps_folder, parents=True, exist_ok=True)
        vtt_path = timestamps_folder / f"{lesson.title}.vtt"
        with vtt_path.open("w", encoding="utf-8") as vtt_file:
            vtt_file.write(lesson.timestamps)


if __name__ == "__main__":
    # Test getting a single lesson
    async def get_lesson_async_tmp(
        language_code: str,
        lesson_id: str,
        download_audio: bool,
        download_timestamps: bool,
        verbose: bool,
    ) -> Lesson:
        async with LingqHandler(language_code) as handler:
            return await get_lesson_async(
                handler, lesson_id, download_audio, download_timestamps, verbose
            )

    lesson = asyncio.run(
        get_lesson_async_tmp(
            language_code="el",
            lesson_id="5897069",
            download_audio=True,
            download_timestamps=True,
            verbose=True,
        )
    )
    write_lesson(
        language_code="el",
        lesson=lesson,
        opath=Path("downloads"),
    )
