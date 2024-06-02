import asyncio
import os

import aiohttp
from lingqhandler import LingqHandler
from utils import Colors, double_check, read_sorted_folders, timing  # type: ignore

SUPPORTED_BY_US_TEXT_EXTENSIONS = [".txt", ".srt"]
SUPPORTED_BY_LINGQ_AUDIO_EXTENSIONS = [".mp3", ".m4a"]

Pairings = list[tuple[str, str | None]]


async def post_lesson(
    handler: LingqHandler,
    course_id: str,
    texts_folder: str,
    text_filename: str,
    audios_folder: str | None = None,
    audio_filename: str | None = None,
) -> None:
    title = None
    data = {
        "collection": course_id,
        "save": "true",
        "description": "Uploaded with https://github.com/daxida/lingq",
    }
    fdata = aiohttp.FormData()
    for key, value in data.items():
        fdata.add_field(key, value)

    # Load text in fdata
    text_filename_clean, text_extension = os.path.splitext(text_filename)
    title = text_filename_clean
    file_path = os.path.join(texts_folder, text_filename)
    fdata.add_field("title", title)
    if text_extension == ".txt":
        fdata.add_field("text", open(file_path, "r", encoding="utf-8").read())
    elif text_extension == ".srt":
        srt_file = open(file_path, "r", encoding="utf-8").read()
        fdata.add_field(
            "file", srt_file, filename="audio.srt", content_type="application/octet-stream"
        )
    else:
        raise NotImplementedError(f"Unsupported text extension: {text_extension}")

    # (Optional) load audio in fdata
    if audio_filename:
        assert audios_folder is not None
        audio_extension = os.path.splitext(audio_filename)[1]
        assert (
            audio_extension in SUPPORTED_BY_LINGQ_AUDIO_EXTENSIONS
        ), f"Unsupported by LingQ audio extension: {audio_extension}"
        file_path = os.path.join(audios_folder, audio_filename)
        audio_file = open(file_path, "rb")
        fdata.add_field(
            "audio", audio_file, filename=f"audio{audio_extension}", content_type="audio/mpeg"
        )

    response = await handler.post_from_multipart(fdata)
    with_audio = "with audio " if audio_filename else ""
    if response.status == 201:
        print(f"  {Colors.OK}[OK]{Colors.END} Posted lesson {with_audio}'{title}{text_extension}'")
    else:
        print(
            f"  {Colors.FAIL}[FAIL]{Colors.END} Failed to post lesson {with_audio}'{title}{text_extension}'"
        )


def apply_pairing_strategy(strategy: str, texts: list[str], audios: list[str]) -> Pairings:
    n_pairs = 0

    if strategy == "zip":
        pairs = list(zip(texts, audios))
        n_pairs = len(pairs)
        print(f"Found {len(pairs)} pairs of texts ({len(texts)}) / audio ({len(audios)}).")
    elif strategy == "match_exact_titles":
        # Remove extensions for comparison
        raw_texts_titles = [os.path.splitext(text_filename)[0] for text_filename in texts]
        raw_audios_titles = [os.path.splitext(audio_filename)[0] for audio_filename in audios]
        text_extension = os.path.splitext(texts[0])[1]
        audio_extension = os.path.splitext(audios[0])[1]

        pairs: Pairings = list()
        for raw_text_filename in raw_texts_titles:
            audio_filename = None
            if raw_text_filename in raw_audios_titles:
                audio_filename = f"{raw_text_filename}{audio_extension}"
                n_pairs += 1
            pairs.append((f"{raw_text_filename}{text_extension}", audio_filename))

        info = ""
        suggestion = ""
        if n_pairs == 0:
            info = f"{Colors.WARN}WARN{Colors.END}: "
            suggestion = " Maybe try a different pairing strategy?"
        print(
            f"{info}Found {n_pairs} matching pairs of texts ({len(texts)}) / audio ({len(audios)}).{suggestion}"
        )

    else:
        raise NotImplementedError

    print("Found the following pairing:")
    for idx, (text, audio) in enumerate(pairs):
        print(f"  ({idx}) {text} ==> {audio}")

    double_check()

    return pairs


async def post_texts(
    handler: LingqHandler, course_id: str, texts: list[str], texts_folder: str
) -> None:
    for text_filename in texts:
        await post_lesson(
            handler, course_id, texts_folder=texts_folder, text_filename=text_filename
        )


async def post_texts_and_audios(
    handler: LingqHandler,
    course_id: str,
    texts: list[str],
    audios: list[str],
    texts_folder: str,
    audios_folder: str,
    pairing_strategy: str,
) -> None:
    pairs = apply_pairing_strategy(pairing_strategy, texts, audios)
    for text_filename, audio_filename in pairs:
        await post_lesson(
            handler,
            course_id,
            texts_folder=texts_folder,
            text_filename=text_filename,
            audios_folder=audios_folder,
            audio_filename=audio_filename,
        )


async def _post(
    language_code: str,
    course_id: str,
    texts_folder: str,
    audios_folder: str | None,
    fr_lesson: int,
    to_lesson: int,
    pairing_strategy: str,
) -> None:
    async with LingqHandler(language_code) as handler:
        url = f"https://www.lingq.com/en/learn/{language_code}/web/editor/courses/{course_id}"
        print(f"Starting upload at {url}")

        texts = read_sorted_folders(texts_folder, mode="human")
        texts = texts[fr_lesson - 1 : to_lesson]
        to_lesson = len(texts)

        texts_extensions = [os.path.splitext(text)[1] for text in texts]
        assert (
            len(set(texts_extensions)) == 1
        ), "All the texts must have the same extension (.txt, .srt)"

        texts_extension = texts_extensions[0]
        assert (
            texts_extension in SUPPORTED_BY_US_TEXT_EXTENSIONS
        ), f"Unsupported text extension: {texts_extension}"

        print(f"Detected '{texts_extension}' extension.")

        if audios_folder:
            audios = read_sorted_folders(audios_folder, mode="human")
            audios = audios[fr_lesson - 1 : to_lesson]
            print(f"Posting text and audio for lessons {fr_lesson} to {to_lesson}...")
            await post_texts_and_audios(
                handler,
                course_id,
                texts,
                audios,
                texts_folder,
                audios_folder,
                pairing_strategy,
            )
        else:
            if texts_extension == ".srt":
                assert audios_folder is not None, "SRT files require audios."
            print(f"Posting text for lessons {fr_lesson} to {to_lesson}...")
            await post_texts(handler, course_id, texts, texts_folder)


@timing
def post(
    language_code: str,
    course_id: str,
    texts_folder: str,
    audios_folder: str | None = None,
    fr_lesson: int = 1,
    to_lesson: int = 99,
    pairing_strategy: str = "match_exact_titles",
):
    """
    Posts preprocessed split text and audio files to a specified course.

    The preprocessed split text (.txt or .srt) files should be in texts_folder,
    and the audio (.mp3 or .m4a) files should be in audios_folder.

    Args:
        language_code (str): The language code of the course.
        course_id (str): The ID of the course. This is the last number in the course URL.
        texts_folder (str): The folder containing the preprocessed split text files.
        audios_folder (str, optional): The folder containing the audio files.
            Set this to None to post only text.
            Defaults to None.
        fr_lesson (int): The index of the first lesson to post (1-indexed).
            Defaults to 1.
        to_lesson (int): The index of the last lesson to post (1-indexed).
            Set to a high number to post everything.
            Defaults to 99.
        pairing_strategy (str, optional): How to pair text and audio files.
            Options are:
            - "zip": Simple zip of files.
            - "match_exact_titles": Group texts and audios with the same title.
                This will post texts if no corresponding audio is found,
                and ignore audios with no corresponding texts.
            Defaults to "match_exact_titles".
    """
    asyncio.run(
        _post(
            language_code,
            course_id,
            texts_folder,
            audios_folder,
            fr_lesson,
            to_lesson,
            pairing_strategy,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    post(
        language_code="ja",
        course_id="537808",
        texts_folder="downloads/srt/",  # "downloads/ja/日本語の森  - JPLT/texts",
        audios_folder="downloads/wav/",  # "downloads/ja/日本語の森  - JPLT/audios",
        fr_lesson=1,
        to_lesson=2,
        pairing_strategy="match_exact_titles",
    )
