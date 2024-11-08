"""
Script to prompt tailored questions based on the subtitles of a youtube video.
It takes as parameters the number of questions to generate.

Uses yt_dlp to download the subtitles.
> pip install yt-dlp
Uses GPT4All to prompt the questions.
> pip install gpt4all
"""

import argparse
import subprocess
from pathlib import Path

from gpt4all import GPT4All


# Function to download YouTube subtitles using yt-dlp
def download_subtitles(video_url: str, lang: str = "ja") -> Path | None:
    """Download YouTube's video's subtitles using yt-dlp"""
    print(f"[yt-dlp] Downloading subtitles for: {video_url}")
    # fmt: off
    command = [
        "yt-dlp",
        "--quiet", "--no-warnings",  # Silence their logger and warnings
        "--write-subs",
        "--sub-lang", lang,          # Download subtitles in lang
        "--skip-download",           # Don't download the video, only subtitles
        "--output",
        "%(title)s.%(ext)s",
        video_url,
    ]
    # fmt: on
    try:
        # If it succeeds, a .vtt file will be created where this script was called.
        subprocess.run(command, check=True)
        print("[yt-dlp] Successfully downloaded subtitles")
        # Find the subtitle file
        subtitles_path = next(f for f in Path().iterdir() if f.suffix == ".vtt")
        return subtitles_path
    except Exception as e:
        print(f"Error downloading subtitles: {e}")
        print("Do you have yt-dlp installed?")


def clean_subtitles(subtitles_path: Path) -> str:
    """Clean .vtt subtitle files (remove timestamps, metadata)"""
    with subtitles_path.open("r", encoding="utf-8") as file:
        lines = file.readlines()

    clean_lines = []
    for line in lines:
        if not line.startswith("WEBVTT") and "-->" not in line:
            clean_lines.append(line.strip())

    return " ".join(clean_lines)


def generate_questions(subtitle_text: str, num_questions: int) -> str:
    model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf")

    # There is a 2048 context window in LLaMA
    char_limit = 2500
    subtitle_text = subtitle_text[:char_limit]
    prompt = (
        f"このテキストに基づいて、日本語で{num_questions}つの質問を作成してください: \n\n"
        f"{subtitle_text}\n\n "
        "質問:"
    )

    print("[gpt4all] Prompting GPT4All to generate questions...")
    response = model.generate(prompt)
    return response


def main(video_url: str, n_questions: int) -> None:
    # Step 1: Download subtitles
    subtitles_path = download_subtitles(video_url)
    if subtitles_path is None:
        print("Subtitle download failed.")
        return

    # Step 2: Clean subtitle file
    subtitle_text = clean_subtitles(subtitles_path)
    if not subtitle_text:
        print("No subtitles found.")
        return

    # Step 3: Generate questions using GPT4All
    questions = generate_questions(subtitle_text, n_questions)
    print("\nGenerated Questions:\n")
    print(questions)

    # Clean up subtitle file
    Path.unlink(subtitles_path)


def parse_args():  # noqa: ANN201
    parser = argparse.ArgumentParser()
    parser.add_argument("video_url", help="URL of the YouTube video")
    parser.add_argument(
        "n_questions",
        type=int,
        nargs="?",
        default=5,
        help="Number of questions to generate (default: 5)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # main(
    #     video_url="https://www.youtube.com/watch?v=3yQetQBlcNg&ab_channel=MikuRealJapanese",
    #     n_questions=4,
    # )
    args = parse_args()
    main(args.video_url, args.n_questions)
