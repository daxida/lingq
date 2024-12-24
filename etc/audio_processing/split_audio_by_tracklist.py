"""Split audio by a Youtube-like formatted tracklist.

Outputs the split audio in the same folder as the audio file to be split.

It should also work for videos but I am not concerned.

Originally from:
https://gist.github.com/Ashwinning/a9677b5b3afa426667d979b36c019b04
"""

import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split audio by tracklist (Youtube-format).")
    parser.add_argument("audio_path", type=Path, help="Path to the audio file")
    parser.add_argument("tracklist_path", type=Path, help="Path to the tracklist file")
    return parser.parse_args()


def remove_symbols(text: str, *, escape_list: list[str] = ["?"]) -> str:
    # ffmpeg did not like having '?' in the file name
    for symbol in escape_list:
        text = text.replace(symbol, "")
    return text


class Track:
    def __init__(self, timestamp: str, name: str) -> None:
        self.timestamp = timestamp
        self.name = name


def extract_tracks(tracklist_path: Path) -> list[Track]:
    tracklist = []
    with tracklist_path.open() as tl:
        for line in tl.readlines():
            name = ""
            timestamp = ""
            for word in line.split(" "):
                if ":" in word:
                    timestamp = word
                else:
                    name += word + " "
            tracklist.append(Track(timestamp, name))

    return tracklist


def get_cmd(
    start: str,
    end: str,
    filename: str,
    audio_path: Path,
    opath: Path,
) -> list[str]:
    return [
        "ffmpeg",
        "-i",
        str(audio_path),
        "-ss",
        start,
        "-to",
        end,
        "-c",
        "copy",
        str(opath / f"{filename}.mp3"),
        "-v",
        "error",
    ]


def get_audio_end(audio_path: Path) -> str:
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        "-sexagesimal",
        str(audio_path),
    ]
    output = subprocess.check_output(ffprobe_cmd).strip()
    end = output.decode("ascii")  # b'5:53:46.272000' -> 5:53:46.272000
    return end


def main() -> None:
    args = parse_args()

    tracklist = extract_tracks(args.tracklist_path)

    opath = args.audio_path.parent / "split_audios"
    opath.mkdir(exist_ok=True)

    for i in range(len(tracklist)):
        filename = tracklist[i].name.strip()
        filename = remove_symbols(filename)
        start = tracklist[i].timestamp.strip()
        if i != len(tracklist) - 1:
            end = tracklist[i + 1].timestamp.strip()  # - startTime
        else:
            end = get_audio_end(args.audio_path)  # - startTime

        print(f"Generating {filename} from {start} to {end}")

        cmd = get_cmd(str(start), str(end), filename, args.audio_path, opath)
        _output = subprocess.check_call(cmd)

    print(f"Wrote split audios at {opath}")


if __name__ == "__main__":
    main()
