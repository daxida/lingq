"""
Download a youtube playlist, generating subtitles if necessary with whisper.

"""

from typing import Dict, Any
from transcriber import Transcriber
import os
import yt_dlp  # type: ignore

PLAYLIST_URL = "https://www.youtube.com/..."

SKIP_DOWNLOADED = True
DOWNLOAD_FOLDER = "downloads"
WHISPER_MODEL = "large"

YELLOW = "\033[33m"
RESET = "\033[0m"


def get_audio_with_subtitles(entry: Any, skip_downloaded: bool) -> None:
    title = entry["title"]
    wav_path = f"{DOWNLOAD_FOLDER}/wav/{title}.wav"
    srt_path = f"{DOWNLOAD_FOLDER}/srt/{title}.srt"
    os.makedirs(f"{DOWNLOAD_FOLDER}/srt", exist_ok=True)
    entry["transcribed_by_whisper_srt_path"] = srt_path

    download_audio(entry, wav_path, "wav", skip_downloaded)
    write_whisper_subtitles(entry, srt_path, wav_path, skip_downloaded)


def download_audio(entry: Any, wav_path: str, format: str, skip_downloaded: bool) -> None:
    if skip_downloaded and os.path.exists(wav_path):
        print(f"{YELLOW}[skip download: found audio]{RESET} {entry['title']}")
        return

    ydl_opts = {
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": format,
            }
        ],
        "outtmpl": wav_path.split(".")[0],  # Remove the .format extension
    }
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
    ydl.download([video_url])  # type: ignore


def write_whisper_subtitles(
    entry: Any, srt_path: str, wav_path: str, skip_downloaded: bool
) -> None:
    if skip_downloaded and os.path.exists(srt_path):
        print(f"{YELLOW}[skip transcription: found srt]{RESET} {entry['title']}")
        return

    transcriber = Transcriber(wav_path, srt_path, WHISPER_MODEL)
    transcriber.transcribe(entry)


def get_playlist(url: str, ydl_opts: Dict[str, Any]) -> Any:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info: Any = ydl.extract_info(url, download=False)  # type: ignore
        sanitized: Any = ydl.sanitize_info(info)  # type: ignore
        # import json
        # print(json.dumps(sanitized, indent=2))  # DEBUG

        return sanitized


def main():
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

    playlist_data = get_playlist(PLAYLIST_URL, ydl_opts)
    entries = playlist_data["entries"]
    for entry in entries:
        get_audio_with_subtitles(entry, SKIP_DOWNLOADED)


if __name__ == "__main__":
    main()
