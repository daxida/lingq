"""
Download a youtube playlist and generate subtitles with whisper.

https://forum.lingq.com/t/easy-whisper-text-generation-from-audio/76701/3
https://github.com/m1guelpf/auto-subtitle
"""

from pathlib import Path
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
    opath: Path,
    whisper_model: str,
    audio_format: str,
) -> None:
    title = entry["title"]
    audio_path = opath / "audios" / f"{title}.{audio_format}"
    srt_path = opath / "texts" / f"{title}.srt"
    entry["transcribed_by_whisper_srt_path"] = srt_path

    download_audio(entry, audio_path, audio_format, skip_downloaded)
    write_whisper_subtitles(entry, whisper_model, srt_path, audio_path, skip_downloaded)


def download_audio(entry: Any, audio_path: Path, format: str, skip_downloaded: bool) -> None:
    if skip_downloaded and audio_path.exists():
        print(f"{Colors.SKIP}[skip download: found audio]{Colors.END} {entry['title']}")
        return

    ydl_opts = {
        "quiet": True,
        "verbose": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
            }
        ],
        "outtmpl": str(audio_path.with_suffix("")),  # Remove the .format extension
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    ydl.download([video_url])  # type: ignore


def write_whisper_subtitles(
    entry: Any, whisper_model: str, srt_path: Path, audio_path: Path, skip_downloaded: bool
) -> None:
    if skip_downloaded and srt_path.exists():
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
    opath: Path,
    whisper_model: str,
    audio_format: str,
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
    text_folder_path = opath / "texts"
    Path.mkdir(text_folder_path, parents=True, exist_ok=True)

    for entry in entries:
        get_audio_with_subtitles(
            entry,
            skip_downloaded,
            opath,
            whisper_model,
            audio_format,
        )


if __name__ == "__main__":
    # Defaults for manually running this script.
    main(
        # playlist_url="https://www.youtube.com/...",
        playlist_url="https://www.youtube.com/playlist?list=PLRaS49ob6Wpnu3pRU_w99w_PPoiQQny15",
        skip_downloaded=True,
        opath=Path("downloads/yt"),
        whisper_model="tiny",
        audio_format="mp3",
    )
