"""Bulk post utilities.

Note: Posting only audio triggers whisper transcript generation on their servers.
"""

import asyncio
from pathlib import Path
from typing import Literal

import aiohttp
import Levenshtein

from lingq.lingqhandler import LingqHandler
from lingq.log import logger
from lingq.utils import double_check, get_editor_url, sorted_subpaths, timing

SUPPORTED_BY_LINGQ_AUDIO_EXTENSIONS = [".mp3", ".m4a"]
SUPPORTED_BY_US_TEXT_EXTENSIONS = [".txt", ".srt", ".vtt"]
SUPPORTED_BY_US_AUDIO_EXTENSIONS = SUPPORTED_BY_LINGQ_AUDIO_EXTENSIONS
PAIRING_STRATEGIES = ["zip", "zipsort", "exact", "fuzzy"]

Strategy = Literal["zip", "zipsort", "exact", "fuzzy"]
Pairing = tuple[Path | None, Path | None]
Pairings = list[Pairing]


class UnsupportedExtensionError(Exception):
    def __init__(self, extension: str) -> None:
        super().__init__(
            f"Unsupported extension '{extension}'\n"
            f"Supported text: {', '.join(SUPPORTED_BY_US_TEXT_EXTENSIONS)} | "
            f"Audio: {', '.join(SUPPORTED_BY_US_AUDIO_EXTENSIONS)}"
        )


async def post_lesson(
    handler: LingqHandler,
    course_id: int,
    tpath: Path | None,
    apath: Path | None,
) -> None:
    # Try first the stem of the text path and fall back on the audio
    title = tpath.stem if tpath else apath.stem if apath else "No title"
    data: dict[str, str] = {
        "title": title,
        "collection": str(course_id),
        "save": "true",
        "description": "Uploaded with https://github.com/daxida/lingq",
    }
    fdata = aiohttp.FormData(data)

    if tpath:
        text = tpath.open("r", encoding="utf-8").read()
        match tpath.suffix:
            case ".txt":
                fdata.add_field("text", text)
            case ".srt":
                fdata.add_field(
                    "file",
                    text,
                    filename=f"text.{tpath.suffix}",
                    content_type="application/octet-stream",
                )
            case ".vtt":
                fdata.add_field(
                    "file", text, filename=f"text.{tpath.suffix}", content_type="text/vtt"
                )
            case _:
                raise UnsupportedExtensionError(tpath.suffix)

    if apath:
        audio_file = apath.open("rb")
        fdata.add_field(
            "audio", audio_file, filename=f"audio.{apath.suffix}", content_type="audio/mpeg"
        )

    response = await handler.post_from_multipart(fdata, raw=True)

    if apath and tpath:
        detail = "(audio and text)"
    elif apath:
        detail = "(audio)"
    else:
        detail = "(text)"

    if response.status == 201:
        logger.success(f"Posted: '{title}' {detail}")
    else:
        logger.error(f"Failed: '{title}' {detail}")


def apply_pairing_strategy(
    pairing_strategy: Strategy, texts_paths: list[Path], audios_paths: list[Path]
) -> Pairings:
    if not texts_paths:
        return [(None, apath) for apath in audios_paths]
    if not audios_paths:
        return [(tpath, None) for tpath in texts_paths]

    pairs: Pairings = []

    match pairing_strategy:
        case "zip":
            pairs = list(zip(texts_paths, audios_paths))
        case "zipsort":
            pairs = list(zip(sorted(texts_paths), sorted(audios_paths)))
        case "exact":
            pairs = exact_match_pairing(texts_paths, audios_paths)
        case "fuzzy":
            pairs = fuzzy_match_pairing(texts_paths, audios_paths)

    n_pairs = sum(all(pair) for pair in pairs)

    logger.info(
        f"Found {n_pairs} pairs of texts ({len(texts_paths)}) / audio ({len(audios_paths)}) "
        f"({pairing_strategy} strategy)."
    )
    if n_pairs == 0:
        logger.warning("No pairings: maybe try a different pairing strategy?")

    for idx, (tpath, apath) in enumerate(pairs):
        print(f"  ({idx}) {tpath.stem if tpath else None} ==> {apath.stem if apath else None}")

    double_check()

    return pairs


def exact_match_pairing(texts_paths: list[Path], audios_paths: list[Path]) -> Pairings:
    pairs: Pairings = []
    for text_path in texts_paths:
        matching_audio_path = None
        for audio_path in audios_paths:
            if text_path.stem == audio_path.stem:
                matching_audio_path = audio_path
                break
        pairs.append((text_path, matching_audio_path))
    return pairs


def fuzzy_match_pairing(
    texts_paths: list[Path], audios_paths: list[Path], max_distance: int = 5
) -> Pairings:
    pairs: Pairings = []
    for text_path in texts_paths:
        best_match = None
        best_distance = max_distance + 1
        for audio_path in audios_paths:
            distance = Levenshtein.distance(text_path.stem, audio_path.stem)
            if distance < best_distance:
                best_match = audio_path
                best_distance = distance
        if best_distance <= max_distance:
            pairs.append((text_path, best_match))
        else:
            pairs.append((text_path, None))
    return pairs


def check_extensions(paths: list[Path], supported: list[str]) -> list[str]:
    """Check if the extensions are supported.

    Ignores folders (i.e. folders inside the audio/text folder).
    """
    extensions = list({path.suffix for path in paths})
    for ext in extensions:
        if ext != "" and ext not in supported:
            raise UnsupportedExtensionError(ext)
    return extensions


async def post_async(
    lang: str,
    course_id: int,
    texts_folder: Path | None,
    audios_folder: Path | None,
    pairing_strategy: Strategy,
) -> None:
    if pairing_strategy not in PAIRING_STRATEGIES:
        raise NotImplementedError(f"Pairing strategy: '{pairing_strategy}' does not exist.")
    if not texts_folder and not audios_folder:
        raise ValueError("Post needs either texts or audios")

    texts_paths = []
    audios_paths = []

    if texts_folder:
        texts_paths = sorted_subpaths(texts_folder, mode="human")
        text_extensions = check_extensions(texts_paths, SUPPORTED_BY_US_TEXT_EXTENSIONS)
        logger.debug(f"Detected text extensions: {', '.join(text_extensions)}")
    if audios_folder:
        audios_paths = sorted_subpaths(audios_folder, mode="human")
        audio_extensions = check_extensions(audios_paths, SUPPORTED_BY_US_AUDIO_EXTENSIONS)
        logger.debug(f"Detected audio extensions: {', '.join(audio_extensions)}")

    pairings = apply_pairing_strategy(pairing_strategy, texts_paths, audios_paths)

    editor_url = get_editor_url(lang, course_id, "course")
    logger.info(f"Uploading at {editor_url}")
    async with LingqHandler(lang) as handler:
        for tpath, apath in pairings:
            await post_lesson(handler, course_id, tpath, apath)


@timing
def post(
    lang: str,
    course_id: int,
    texts_folder: Path,
    audios_folder: Path | None = None,
    pairing_strategy: Strategy = "exact",
) -> None:
    """Posts preprocessed split text and audio files to a specified course.

    The preprocessed split text (.txt or .srt) files should be in texts_folder,
    and the audio (.mp3 or .m4a) files should be in audios_folder.

    Args:
        lang (str): The language code of the course.
        course_id (int): The ID of the course. This is the last number in the course URL.
        texts_folder (Path): The folder containing the preprocessed split text files.
        audios_folder (Path, optional): The folder containing the audio files.
            Set this to None to post only text.
            Defaults to None.
        pairing_strategy (str, optional): How to pair text and audio files.
            Options are: ["zip", "zipsort", "exact", "fuzzy"]
    """
    asyncio.run(
        post_async(
            lang,
            course_id,
            texts_folder,
            audios_folder,
            pairing_strategy,
        )
    )


if __name__ == "__main__":
    # Defaults for manually running this script.
    post(
        lang="ja",
        course_id=537808,
        texts_folder=Path("downloads/ja/Quick Imports/texts"),
        # texts_folder=Path("downloads/ja/Quick Imports/texts"),
        audios_folder=Path("downloads/ja/Quick Imports/audios"),
        # audios_folder=None,
        # pairing_strategy="zip",
        pairing_strategy="fuzzy",
    )
