"""Forced alignment: split audio (one or more files) to match text (one or more files).

NOTE: This script requires the library aeneas. Since it is not trivial to install, it is
      not included in the manifest. A (sort of) installation guide can be found below this
      docstring but first you should read this script description to verify that this solves
      your problem.

This assumes:

(1) A particular file structure:
    example
    ├── texts
    │   ├── text1.txt
    │   └── text2.txt
    └── audios
        ├── audio1.mp3
        ├── audio2.mp3
        └── audio3.mp3
(2) Of ordered text and audios. That is, the contents of the text files must be in
    ascending order, i.e. the contents of text2.txt should come AFTER those of text1.txt etc.
    The same should hold for the audio files.

You may find yourself in one of this cases:

(1) Your texts and audios are chapter-structured.
    Then you don't need any of this and you can just post your pairing to LingQ.
(2) Your texts are chapter-structured but your audios are NOT.
    In this case you would want to split with "Preserving chapters" with simply:
    process_files(
        language="ell",
        files_dir="my_input_files",
    )
    This only modifies audios.
(3) Your texts and audios are NOT chapter-structured.
    If you want them to be chapter-structured, this (and most likely no tool out there) does
    not support it. You will have to manually taylor your particular case.
    If instead you want to split it in a number of sections to adapt the length to your needs
    you can by either:
    process_files(
        language="ell",
        files_dir="my_input_files",
        n_sections=10, # At most 10 sections
    )

    Or if you have a number of seconds per section in mind:
    process_files(
        language="ell",
        files_dir="my_input_files",
        cut_at_seconds=30, # At least 30 seconds
    )
    This modifies texts and audios.

----------- Aeneas

https://github.com/readbeyond/aeneas

Their listed requirements:
https://github.com/readbeyond/aeneas?tab=readme-ov-file#system-requirements

Install guide:
https://github.com/readbeyond/aeneas/blob/master/wiki/INSTALL.md

OBSOLETE: I am using the fork now!!

Aeneas turns out to be sort of tricky to set up.
You don't have to follow this, it is mostly for self-reference. What I ended up doing:

- gh repo clone readbeyond/aeneas
- cd aeneas
- https://github.com/readbeyond/aeneas/issues/306#issuecomment-2212360050
    - At setup.py comment line 200: "from numpy.distutils import misc_util"
    - At setup.py replace line 208 with: "INCLUDE_DIRS = [get_include()]"
- https://github.com/readbeyond/aeneas/pull/272
    - Add a pyproject.toml with:
    [build-system]
    requires = ["setuptools", "wheel", "numpy>=1.9"]
- Then, as they state in the guide:
    pip install -r requirements.txt \
    pip install setuptools \
    python setup.py build_ext --inplace \
    python aeneas_check_setup.py \
    pip install .
- You can now delete the aeneas repo.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aeneas.executetask import ExecuteTask, RuntimeConfiguration
from aeneas.logger import Logger
from aeneas.task import Task
from loguru import logger
from mutagen.mp3 import MP3

# TODO: format the original text so that the merged text is sentence-separated.
#       Since aeneas will match the text chunks, this will make the timestamps
#       be precise at sentence level.
#       One has to be careful then at split_audio_by_preserving_chapters to match
#       the correct sentence.


@dataclass
class TimedText:
    """Text with timestamp.

    The text is the output unit of split audio.
    In default mode, it represents a chapter and may contain newlines.
    """

    title: str
    begin: str
    end: str
    text: str


logger_format = "  | <level>{message}</level>"
logger.remove()
logger.add(sys.stderr, format=logger_format)
logger.add("logs_fa.log", rotation="10 MB", retention="7 days")
logging = logger


def align_audio_to_text(
    audio_path: Path,
    text_path: Path,
    opath: Path,
    lang: str,
    *,
    verbose: bool = False,
) -> None:
    """Send alignment task to Aeneas."""
    # TODO: Test removing silences!
    logging.info(f"Start alignment for audio: {audio_path} and text: {text_path}")

    aeneas_logger = Logger(tee=verbose)

    # https://groups.google.com/g/aeneas-forced-alignment/c/J7FnZ8OSOLE
    # For a parameters list:
    # python3 -m aeneas.tools.execute_task --list-parameters
    config = [
        # -- Required
        f"task_language={lang}",
        "is_text_type=plain",
        "os_task_file_format=json",
        # -- Optional
        # Do not allow zero-length fragments
        # "task_adjust_boundary_no_zero",
        # # Trim nonspeech
        # "task_adjust_boundary_nonspeech_min=0.500",
        # "task_adjust_boundary_nonspeech_string=REMOVE",
    ]
    config_string = "|".join(config)

    rconf = RuntimeConfiguration()
    if lang == "jpn":
        # The default "espeak" does not support japanese
        rconf[RuntimeConfiguration.TTS] = "espeak-ng"
        rconf[RuntimeConfiguration.TTS_PATH] = "/usr/bin/espeak-ng"

    task = Task(config_string=config_string, rconf=rconf, logger=aeneas_logger)
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = text_path
    task.sync_map_file_path_absolute = opath

    # Execute alignment task
    logging.debug(f"Task config: {config_string}")
    logging.debug(
        f"Runtime config: "
        f"TTS={rconf[RuntimeConfiguration.TTS]}|"
        f"TTS_PATH={rconf[RuntimeConfiguration.TTS_PATH]}"
    )
    ExecuteTask(task, rconf=rconf, logger=aeneas_logger).execute()
    task.output_sync_map_file()
    logging.success(f"Finished alignment. Sync map file saved to: {opath}")


def get_mp3_length(file_path: Path) -> float:
    return MP3(file_path).info.length


def seconds_to_hms(seconds_str: str) -> str:
    seconds = int(float(seconds_str))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"


def ffmpeg_split(audio_file: Path, begin: str, end: str, output_audio_path: Path) -> None:
    # fmt: off
    subprocess.run(
        [
            "ffmpeg",
            "-i", audio_file,
            "-ss", begin,
            "-to", end,
            "-c", "copy",
            "-loglevel", "quiet",
            "-y",  # always overwrite
            output_audio_path,
        ]
    )
    # fmt: on


TextLines = tuple[str, list[str]]
"""Text lines. The first item is the name of (usually) the chapter.
Then it contains a list (paragraph) of strings.
"""

TextsLines = list[TextLines]
"""List of TextLines: one per text file read."""


def split_audio(
    fragments: Any, texts_lines: TextsLines, cut_at_seconds: float = 0.0
) -> list[TimedText]:
    """Split audio.

    Note that texts_lines are the original lines (which can differ from the merged
    text in some languages: i.e. japanese)
    """
    # Remove fragments with no text. This may happen if the text has empty lines.
    n_fragments = len(fragments)
    fragments = [fr for fr in fragments if fr["lines"][0]]
    logger.info(f"Discarded {n_fragments - len(fragments)} empty fragments")

    n_paragraphs = sum(len(paragraph) for _, paragraph in texts_lines)

    if len(fragments) != n_paragraphs:
        logging.warning(
            f"The number of non-empty fragments: {len(fragments)} "
            f"is different from the number of paragraphs: {n_paragraphs}"
        )

    if len(fragments) > n_paragraphs:
        raise ValueError(
            f"The number of non-empty fragments: {len(fragments)} "
            f"is bigger than the number of paragraphs: {n_paragraphs}"
        )

    if cut_at_seconds > 0:
        timed_texts = split_audio_by_time(fragments, cut_at_seconds)
    else:
        timed_texts = split_audio_preserving_chapters(fragments, texts_lines)

    logging.success("Finished split audio")

    return timed_texts


def split_audio_preserving_chapters(fragments: Any, texts_lines: TextsLines) -> list[TimedText]:
    """Split audio and text preserving the original text split.

    That is, go back to the unmerged texts and remap the syncmap.

    Since aeneas always chunks by sentences, this should be straightforward.
    """
    logging.info("Start split audio (preserving chapters)")

    # We expect to produce the same amount of chunks as the original
    expected_timed_texts = len(texts_lines)

    fragments_it = enumerate(fragments, start=1)
    fragments_exhausted = False

    last_end = fragments[-1]["end"]
    logging.debug(f"Last end: {last_end} ({seconds_to_hms(last_end)})")
    logging.debug(f"Number of original texts: {expected_timed_texts}")
    reached_last_end = False

    timed_texts = []

    for title, text_lines in texts_lines:
        cur_begin = None
        cur_end = None
        fragment_idxs = []

        for i in range(len(text_lines)):
            try:
                fragment_idx, fragment = next(fragments_it)
            except StopIteration:
                logging.error(
                    "There are more text lines that fragments! "
                    "Is the audio completely covering the text?"
                )
                fragments_exhausted = True
                break

            begin = fragment["begin"]
            end = fragment["end"]
            # lines = fragment["lines"]

            if cur_begin is None:
                cur_begin = begin
            cur_end = end

            fragment_idxs.append(fragment_idx)

            remaining_lines = len(text_lines) - (i + 1)
            if end == last_end and remaining_lines:
                logging.error(
                    f"Reached last end prematurely ({remaining_lines} remaining lines). Exiting"
                )
                reached_last_end = True
                break

        assert cur_begin, "TimedText begin should not be None"
        assert cur_end, "TimedText end should not be None"

        timed_text = TimedText(title, cur_begin, cur_end, "\n".join(text_lines))

        cur_interval = round(float(cur_end) - float(cur_begin), 3)
        logging.debug(
            "(Fragments {:{width}} - {:{width}}) " "{start_time} - {end_time} ({interval}s)".format(
                fragment_idxs[0],
                fragment_idxs[-1],
                width=len(str(len(fragments))),
                start_time=seconds_to_hms(cur_begin),
                end_time=seconds_to_hms(cur_end),
                interval=cur_interval,
            )
        )

        if cur_interval == 0 and timed_text.text:
            # If there is a zero interval timed_text with non-empty text
            # then, most likely, there is a mismatch / the alignment failed.
            ctx = f"{timed_text.text[:200]}{'...' if len(timed_text.text) > 200 else ''}"
            logging.error(f"Zero interval with text for {ctx}")
            break

        timed_texts.append(timed_text)

        if fragments_exhausted or reached_last_end:
            break

    if len(timed_texts) != expected_timed_texts:
        logging.error(
            f"We expected {expected_timed_texts} text chunk(s) but we made {len(timed_texts)}"
        )

    return timed_texts


def split_audio_by_time(fragments: Any, cut_at_seconds: float) -> list[TimedText]:
    """Split audio and text by the given cut_at_seconds.

    That is, if cut_at_seconds=60, it will cut every time we reach > 60secs
    in our current buffer.
    """
    # TODO: split by sentences the original text to see if it improves precision

    logging.info("Start split audio (by time)")

    last_end = fragments[-1]["end"]
    cur_begin = None
    cur_end = None
    fragment_idx = 0
    text_buffer = []
    timed_texts = []
    timed_text_idx = 0

    for fragment in fragments:
        begin = fragment["begin"]
        end = fragment["end"]
        lines = fragment["lines"]

        if not cur_begin:
            cur_begin = begin
        cur_end = end
        cur_interval = round(float(cur_end) - float(cur_begin), 3)

        # Weird that lines is a list(?)
        text_buffer.extend(lines)

        if cur_interval > cut_at_seconds or end == last_end:
            # logging.debug(f"({fragment_idx+1}) {cur_begin} - {cur_end} ({cur_interval=})")
            logging.debug(
                f"({fragment_idx + 1}) "
                f"{seconds_to_hms(cur_begin)} - {seconds_to_hms(cur_end)} ({cur_interval=}s)"
            )

            timed_text = TimedText(
                f"text{timed_text_idx:02d}",
                cur_begin,
                cur_end,
                "\n".join(text_buffer),
            )
            timed_text_idx += 1
            timed_texts.append(timed_text)

            cur_begin = None
            fragment_idx += 1
            text_buffer.clear()

    return timed_texts


def write_timed_texts(timed_texts: list[TimedText], audio_path: Path, output_dir: Path) -> None:
    """Write the timed_texts to disk.

    Uses the timed text title for both the new text and audio.
    """
    logging.info("Writting timed texts")
    for tt in timed_texts:
        opath_audio = output_dir / "audios" / f"{tt.title}.mp3"
        ffmpeg_split(audio_path, tt.begin, tt.end, opath_audio)
        opath_text = output_dir / "texts" / f"{tt.title}.txt"
        with opath_text.open("w") as f:
            f.write(tt.text)


def debug_paths(paths: list[Path] | list[str]) -> str:
    dbg_message = ", ".join(f"'{path}'" for path in paths[:3])
    if len(paths) > 3:
        dbg_message += ", ..."
    return dbg_message


def custom_sort_key(path: Path) -> tuple[int, ...] | str:
    """Generate a sorting key for human sort.

    If the path.name starts with digits (ex. 1.3.1. Title), then compare numbers.
    Otherwise fall back on usual string comparison.
    """
    name = path.name
    if m := re.match(r"^((\d+\.)*\d+)", name):
        nums = m.group(1).split(".")
        return tuple(int(num) for num in nums)
    return name


def get_sorted_file_paths(files_dir: Path, extension: str) -> list[Path]:
    """Get .txt/.mp3 files in texts/audios sorted.

    Uses human sort 1 < 2 < ... < 10 as opposed to string sort
    """
    file_paths = [
        fp for fp in files_dir.iterdir() if fp.suffix == extension and "merged" not in fp.name
    ]
    return sorted(file_paths, key=custom_sort_key)


def merge_texts(merged_text_path: Path, *, lang: str) -> None:
    """Merge all text files into a single one."""
    text_dir = merged_text_path.parent
    text_paths = get_sorted_file_paths(text_dir, ".txt")
    logging.info(f"Merging texts at '{merged_text_path}'")
    logging.debug(f"Text files ({len(text_paths)}): {debug_paths(text_paths)}")
    logging.trace(f"Text files ({len(text_paths)}): {text_paths}")

    if lang == "jap":
        merge_texts_jap(merged_text_path, text_paths)
    else:
        merge_texts_default(merged_text_path, text_paths)


def merge_texts_default(merged_text_path: Path, text_paths: list[Path]) -> None:
    """Merge all text files into a single one."""
    with merged_text_path.open("w", encoding="utf-8") as merged_file:
        for text_file_path in text_paths:
            with text_file_path.open("r", encoding="utf-8") as tf:
                content = tf.read()
                merged_file.write(content)
                merged_file.write("\n")


def merge_texts_jap(merged_text_path: Path, text_paths: list[Path]) -> None:
    """Merge all text files into a single one.

    Convert to hiragana for the TTS to produce audio...
    """
    import pykakasi

    kks = pykakasi.kakasi()

    with merged_text_path.open("w", encoding="utf-8") as merged_file:
        for text_file_path in text_paths:
            with text_file_path.open("r", encoding="utf-8") as tf:
                content = tf.read()

                converted_content = []
                for line in content.splitlines():
                    conv_line = []
                    tokens = kks.convert(line)
                    for token in tokens:
                        if re.match(r"[\u3040-\u30FF\u4E00-\u9FFF]", token["orig"]):
                            tkn = token["hira"]
                        else:
                            tkn = token["orig"]
                        conv_line.append(tkn)
                    converted_content.append(" ".join(conv_line))

                content = "\n".join(converted_content)

                merged_file.write(content)
                # merged_file.write("\n")


def merge_audios(merged_audio_path: Path) -> None:
    """Merge all audio files into a single one."""
    audio_dir = merged_audio_path.parent
    audio_files = [af.name for af in get_sorted_file_paths(audio_dir, ".mp3")]
    logging.info(f"Merging audios at '{merged_audio_path}'")
    logging.debug(f"Audio files ({len(audio_files)}): {debug_paths(audio_files)}")

    # Create a temporary file list for ffmpeg input
    temp_file_list = audio_dir / "mp3_files_to_merge.txt"
    with temp_file_list.open("w", encoding="utf-8") as f:
        for audio_file_name in audio_files:
            f.write(f"file '{audio_file_name}'\n")

    # fmt: off
    subprocess.run(
        [
            "ffmpeg",
            "-f", "concat",         # Use concat demuxer
            "-safe", "0",           # Allow unsafe file paths
            "-i", temp_file_list,   # Input file list
            "-c", "copy",           # Copy streams without re-encoding
            "-loglevel", "quiet",   # Suppress ffmpeg output
            "-y",                   # Overwrite existing output
            merged_audio_path       # Output merged file
        ]
    )
    # fmt: on

    if not merged_audio_path.exists():
        logging.error(f"[merge_audio_files] Could not find the merged file: {merged_audio_path}")
        exit(1)

    # Clean up temporary file list
    Path.unlink(temp_file_list)


def main(
    lang: str,
    files_dir: Path,
    cut_at_seconds: float = 0.0,
    n_sections: int = 0,
) -> None:
    """Align multiple audios and texts.

    - Look for expected input file structure
    - Merge text and audio
    - Deal with cut_at_seconds if needed
    - Setup output file structure
    - Align audio and text
    - Split audio based on sync map
    - Write output
    - Clean up temporary files
    """
    audio_dir = files_dir / "audios"
    text_dir = files_dir / "texts"

    # Merge text and audio
    merged_text_path = text_dir / "text_merged.txt"
    merge_texts(merged_text_path, lang=lang)
    merged_audio_path = audio_dir / "audio_merged.mp3"
    merge_audios(merged_audio_path)

    # If given a number of sections, overwrite cut_at_seconds.
    # Crashes if cut_at_seconds is not its default value of 0.
    if n_sections > 0:
        audio_length = get_mp3_length(merged_audio_path)
        cut_at_seconds = round(audio_length / n_sections, 2)
        logging.debug(f"Given {n_sections=}, the new cut_at_seconds is {cut_at_seconds}")
    cut_at_seconds = float(cut_at_seconds)

    # Setup output file structure
    if cut_at_seconds > 0:
        output_dir = files_dir / f"output_by_time_{cut_at_seconds}"
    else:
        output_dir = files_dir / "output"
    Path.mkdir(output_dir / "audios", parents=True, exist_ok=True)
    Path.mkdir(output_dir / "texts", parents=True, exist_ok=True)

    # Align audio with text using the specified language
    output_json = output_dir / "syncmap.json"
    align_audio_to_text(merged_audio_path, merged_text_path, output_json, lang)

    # Split the audio based on the sync map
    fragments = json.load(output_json.open("r"))["fragments"]
    text_files_paths = get_sorted_file_paths(text_dir, ".txt")
    texts_lines: TextsLines = [
        (fp.stem, fp.open("r", encoding="utf-8").read().strip().splitlines())
        for fp in text_files_paths
    ]

    # For making tests
    # logging.debug(f"{fragments=}")
    # logging.debug(f"{text_files_paths=}")
    # logging.debug(f"{text_files=}")

    timed_texts = split_audio(fragments, texts_lines, cut_at_seconds)
    write_timed_texts(timed_texts, merged_audio_path, output_dir)

    # Remove merged files
    logging.info("Removing merged files")
    for file in (merged_text_path, merged_audio_path):
        Path.unlink(file)

    logging.success(f"Finished. Check '{output_dir}'.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Forced alignment with aeneas.")
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="jpn",
        help="Aeneas language code (e.g., 'ell' for Greek, 'jpn' for Japanese)",
    )
    parser.add_argument(
        "-i",
        "--ipath",
        type=Path,
        default=Path("book"),
        help="Path to the book (e.g., directory containing text/audio files). Default: 'book'",
    )
    parser.add_argument(
        "-c",
        "--cut-at-seconds",
        type=int,
        default=0,
        help="Maximum duration (in seconds) to cut sections",
    )
    parser.add_argument(
        "-n",
        "--n-sections",
        type=int,
        default=0,
        help="Number of sections to split the input into",
    )

    args = parser.parse_args()

    if args.cut_at_seconds > 0 and args.n_sections > 0:
        reason = "cut_at_seconds conflicts with n_sections. Only input one of them."
        raise ValueError(reason)

    return args


if __name__ == "__main__":
    """Replace 'ell' with the language code of your choice.

    List of aeneas' supported languages:
    https://www.readbeyond.it/aeneas/docs/language.html
    """
    args = parse_args()

    tested_langs = {"jpn", "ell"}
    if args.lang not in tested_langs:
        logging.warning(f"Untested language: {args.lang}")

    main(
        lang=args.lang,
        files_dir=args.ipath,
        cut_at_seconds=args.cut_at_seconds,
        n_sections=args.n_sections,
    )
