"""
Forced alignment.
Split audio (one or more files) to match text (one or more files).

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

Aeneas turns out to be sort of tricky to set up.
You don't have to follow this, it is mostly for self-reference. What I ended up doing:

- gh repo clone readbeyond/aeneas
- https://github.com/readbeyond/aeneas/issues/306#issuecomment-2212360050
    - At setup.py comment line 200: "from numpy.distutils import misc_util"
    - At setup.py replace line 208 with: "INCLUDE_DIRS = [get_include()]"
- https://github.com/readbeyond/aeneas/pull/272
    - Add their pyproject.toml
- Then, as they state in the guide:
    cd aeneas
    pip install -r requirements.txt
    pip install setuptools
    python setup.py build_ext --inplace
    python aeneas_check_setup.py
    pip install .
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass

from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from mutagen.mp3 import MP3


@dataclass
class TimedText:
    begin: str
    end: str
    text: str


RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        match record.levelname:
            case "DEBUG":
                record.levelname = f"{BLUE}[{record.levelname}]{RESET}"
            case "INFO":
                record.levelname = f"{GREEN}[{record.levelname}]{RESET}"
            case "ERROR":
                record.levelname = f"{RED}[{record.levelname}]{RESET}"
        return super().format(record)


logging.basicConfig(level=logging.DEBUG)
for handler in logging.getLogger().handlers:
    handler.setFormatter(ColoredFormatter("%(levelname)s %(message)s"))


def align_audio_to_text(audio_file, text_file, opath, language):
    logging.info(f"Starting alignment for audio: {audio_file} and text: {text_file}")

    # Update the task configuration string to use the specified language
    config_string = f"task_language={language}|is_text_type=plain|os_task_file_format=json"
    task = Task(config_string=config_string)
    task.audio_file_path_absolute = audio_file
    task.text_file_path_absolute = text_file
    task.sync_map_file_path_absolute = opath

    # Execute alignment task
    logging.debug(f"Executing alignment task with configuration:\n  {config_string}")
    ExecuteTask(task).execute()
    task.output_sync_map_file()
    logging.debug(f"Alignment task completed. Sync map file saved to: {opath}")


def get_sorted_file_paths(files_dir, extension):
    file_paths = [
        os.path.join(files_dir, fp)
        for fp in os.listdir(files_dir)
        if fp.endswith(extension) and "merged" not in fp
    ]
    return sorted(file_paths)


def get_mp3_length(file_path):
    return MP3(file_path).info.length


def seconds_to_hms(seconds_str):
    seconds = int(float(seconds_str))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02}:{seconds:02}"


def ffmpeg_split(audio_file, begin, end, output_audio_path):
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


def split_audio(fragments, text_files, cut_at_seconds=0.0) -> list[TimedText]:
    logging.info("Start split_audio")

    if cut_at_seconds > 0:
        timed_texts = split_audio_by_time(fragments, cut_at_seconds)
    else:
        timed_texts = split_audio_preserving_chapters(fragments, text_files)

    return timed_texts


def split_audio_preserving_chapters(fragments, text_files):
    """Split audio and text preserving the original text split."""
    logging.info("Start split preserving texts")

    _last_lines = [lines[-1].strip() for lines in text_files]
    last_lines = iter(_last_lines)

    last_end = fragments[-1]["end"]
    cur_begin = None
    cur_end = None
    cur_line = None
    fragment_idx = 0
    text_buffer = []
    timed_texts = []

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

        if not cur_line:
            cur_line = next(last_lines)

        if lines[0] == cur_line or end == last_end:
            # logging.debug(f"({fragment_idx+1}) {cur_begin} - {cur_end} ({cur_interval=})")
            logging.debug(
                f"({fragment_idx+1}) {seconds_to_hms(cur_begin)} - {seconds_to_hms(cur_end)} ({cur_interval=}s)"
            )

            timed_text = TimedText(cur_begin, cur_end, "\n".join(text_buffer))
            timed_texts.append(timed_text)

            cur_begin = None
            fragment_idx += 1
            text_buffer.clear()
            cur_line = None

    return timed_texts


def split_audio_by_time(fragments, cut_at_seconds):
    """Split audio and text by the given cut_at_seconds"""
    # TODO: split by sentences the original text to see if it improves precision

    logging.info("Start split by time")

    last_end = fragments[-1]["end"]
    cur_begin = None
    cur_end = None
    fragment_idx = 0
    text_buffer = []
    timed_texts = []

    for fragment in fragments:
        begin = fragment["begin"]
        end = fragment["end"]
        lines = fragment["lines"]
        # I'm not sure whats the point of aeneas using a list of string for only one string
        assert len(lines) == 1

        if not cur_begin:
            cur_begin = begin
        cur_end = end
        cur_interval = round(float(cur_end) - float(cur_begin), 3)

        # Weird that lines is a list(?)
        text_buffer.extend(lines)

        if cur_interval > cut_at_seconds or end == last_end:
            # logging.debug(f"({fragment_idx+1}) {cur_begin} - {cur_end} ({cur_interval=})")
            logging.debug(
                f"({fragment_idx+1}) {seconds_to_hms(cur_begin)} - {seconds_to_hms(cur_end)} ({cur_interval=}s)"
            )

            timed_text = TimedText(cur_begin, cur_end, "\n".join(text_buffer))
            timed_texts.append(timed_text)

            cur_begin = None
            fragment_idx += 1
            text_buffer.clear()

    return timed_texts


def write_timed_texts(timed_texts, audio_file, output_dir):
    logging.info("Writting timed texts")
    for idx, tt in enumerate(timed_texts, 1):
        output_audio_path = f"{output_dir}/audios/audio{idx}.mp3"
        ffmpeg_split(audio_file, tt.begin, tt.end, output_audio_path)
        output_text_path = f"{output_dir}/texts/text{idx}.txt"
        with open(output_text_path, "w") as f:
            f.write(tt.text)


def merge_text_files(text_dir, merged_text_file):
    """Merge all text files into a single one."""
    text_files = get_sorted_file_paths(text_dir, ".txt")
    logging.debug(f"Text files: {text_files}")

    with open(merged_text_file, "w", encoding="utf-8") as merged_file:
        for text_file_path in text_files:
            with open(text_file_path, "r", encoding="utf-8") as tf:
                content = tf.read()
                merged_file.write(content)
                # merged_file.write("\n")


def merge_audio_files(audio_dir, merged_audio_file):
    """Merge all audio files into a single one."""
    audio_files = get_sorted_file_paths(audio_dir, ".mp3")
    audio_files = [af.split("/")[-1] for af in audio_files]
    logging.debug(f"Audio files: {audio_files}")

    # Create a temporary file list for ffmpeg input
    temp_file_list = os.path.join(audio_dir, "mp3_files_to_merge.txt")
    with open(temp_file_list, "w", encoding="utf-8") as f:
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
            merged_audio_file       # Output merged file
        ]
    )
    # fmt: on

    if not os.path.exists(merged_audio_file):
        logging.error(f"[merge_audio_files] Could not find the merged file: {merged_audio_file}")
        exit(1)

    # Clean up temporary file list
    os.remove(temp_file_list)


def process_files(language, files_dir, cut_at_seconds=0.0, n_sections=0):
    # Setup input file structure
    audio_dir = os.path.join(files_dir, "audios")
    text_dir = os.path.join(files_dir, "texts")

    # Merge text and audio
    merged_text_file = os.path.join(text_dir, "text_merged.txt")
    merge_text_files(text_dir, merged_text_file)
    merged_audio_file = os.path.join(audio_dir, "audio_merged.mp3")
    merge_audio_files(audio_dir, merged_audio_file)

    # If given a number of sections, overwrite cut_at_seconds.
    # Crashes if cut_at_seconds is not its default value of 0.
    if n_sections > 0:
        assert cut_at_seconds == 0
        audio_length = get_mp3_length(merged_audio_file)
        cut_at_seconds = audio_length / n_sections
        logging.debug(f"Given {n_sections=}, the new cut_at_seconds is {cut_at_seconds}")
    cut_at_seconds = float(cut_at_seconds)

    # Setup output file structure
    if cut_at_seconds > 0:
        output_dir = os.path.join(files_dir, f"output_by_time_{cut_at_seconds}")
    else:
        output_dir = os.path.join(files_dir, "output")
    os.makedirs(os.path.join(output_dir, "audios"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "texts"), exist_ok=True)

    # Align audio with text using the specified language
    output_json = os.path.join(output_dir, f"syncmap.json")
    align_audio_to_text(merged_audio_file, merged_text_file, output_json, language)

    # Split the audio based on the sync map
    fragments = json.load(open(output_json, "r"))["fragments"]
    text_files_paths = get_sorted_file_paths(text_dir, ".txt")
    text_files = [
        open(fp, "r", encoding="utf-8").read().strip().splitlines() for fp in text_files_paths
    ]
    # For making tests
    # logging.debug(f"{fragments=}")
    # logging.debug(f"{text_files_paths=}")
    # logging.debug(f"{text_files=}")

    timed_texts = split_audio(fragments, text_files, cut_at_seconds)
    write_timed_texts(timed_texts, merged_audio_file, output_dir)

    # Remove merged files
    logging.info("Removing merged files")
    for file in (merged_text_file, merged_audio_file):
        os.remove(file)


if __name__ == "__main__":
    # Replace 'eng' with the language code of your choice
    # List of aeneas' supported languages: https://www.readbeyond.it/aeneas/docs/language.html
    # TODO: make it work for japanese!
    process_files(
        language="ell",
        files_dir="test_el_1m_3t_2a",
        cut_at_seconds=10,
        # n_sections=20,
    )
    logging.info("Processing complete. Check the 'output' directory for results.")
