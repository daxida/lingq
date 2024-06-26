"""
Download a youtube playlist and generate subtitles with whisper.

https://forum.lingq.com/t/easy-whisper-text-generation-from-audio/76701/3
https://github.com/m1guelpf/auto-subtitle
"""

import os
from typing import Any

import yt_dlp  # type: ignore
from transcriber import Transcriber


class Colors:
    # fmt: off
    FAIL = "\033[31m"    # RED
    OK   = "\033[32m"    # GREEN
    WARN = "\033[33m"    # YELLOW
    SKIP = "\033[0;91m"  # ORANGE
    TIME = "\033[36m"    # CYAN
    END  = "\033[0m"
    # fmt: on


def get_audio_with_subtitles(
    entry: Any,
    skip_downloaded: bool,
    download_folder: str,
    whisper_model: str,
    audio_format: str,
    srt_folder: str,
    audio_folder: str,
) -> None:
    title = entry["title"]
    audio_path = os.path.join(download_folder, audio_folder, f"{title}.{audio_format}")
    srt_path = os.path.join(download_folder, srt_folder, f"{title}.srt")
    entry["transcribed_by_whisper_srt_path"] = srt_path

    download_audio(entry, audio_path, audio_format, skip_downloaded)
    write_whisper_subtitles(entry, whisper_model, srt_path, audio_path, skip_downloaded)


def download_audio(entry: Any, audio_path: str, format: str, skip_downloaded: bool) -> None:
    if skip_downloaded and os.path.exists(audio_path):
        print(f"{Colors.SKIP}[skip download: found audio]{Colors.END} {entry['title']}")
        return

    ydl_opts = {
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
            }
        ],
        "outtmpl": os.path.splitext(audio_path)[0],  # Remove the .format extension
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    ydl.download([video_url])  # type: ignore


def write_whisper_subtitles(
    entry: Any, whisper_model: str, srt_path: str, audio_path: str, skip_downloaded: bool
) -> None:
    if skip_downloaded and os.path.exists(srt_path):
        print(f"{Colors.SKIP}[skip transcription: found srt]{Colors.END} {entry['title']}")
        return

    transcriber = Transcriber(audio_path, srt_path, whisper_model)
    transcriber.transcribe(entry)


def get_playlist(url: str, ydl_opts: dict[str, Any]) -> Any:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: Any = ydl.extract_info(url, download=False)  # type: ignore
        sanitized: Any = ydl.sanitize_info(info)  # type: ignore
        # import json
        # print(json.dumps(sanitized, indent=2))  # DEBUG

        return sanitized


def main(
    playlist_url: str,
    skip_downloaded: bool,
    download_folder: str,
    whisper_model: str,
    audio_format: str,
    srt_folder: str,
    audio_folder: str,
) -> None:
    ydl_opts = {
        # Set title language "extractor_args": {"youtube": {"lang": ["zh-TW"]}},
        # "forceprint": {"video": ["title", "url"]}, # DEBUG
        "quiet": True,
        # "simulate": True, # not needed if .extract_info(download=False)
        # If a playlist has private videos, '"ignoreerrors": True' will crash the whole
        # program. If you know it hasn't, you would probably want this set to 'False'.
        "ignoreerrors": True,
        "verbose": False,
    }

    playlist_data = get_playlist(playlist_url, ydl_opts)
    entries = playlist_data["entries"]
    os.makedirs(os.path.join(download_folder, srt_folder), exist_ok=True)

    for entry in entries:
        get_audio_with_subtitles(
            entry,
            skip_downloaded,
            download_folder,
            whisper_model,
            audio_format,
            srt_folder,
            audio_folder,
        )


if __name__ == "__main__":
    # Defaults for manually running this script.
    main(
        playlist_url="https://www.youtube.com/...",
        skip_downloaded=True,
        download_folder="downloads/yt",
        whisper_model="tiny",
        audio_format="mp3",
        srt_folder="texts",
        audio_folder="audios",
    )
