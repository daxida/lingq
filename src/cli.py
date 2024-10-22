import os

import click
from generate_timestamps import generate_timestamps
from get_courses import get_courses
from get_lessons import get_lessons
from get_pictures import get_pictures
from get_words import get_words
from library_overview import overview
from make_markdown import make_markdown
from patch import patch_audios
from post import post
from post_yt_playlist import post_yt_playlist
from resplit import resplit
from show import show_my
from sort_lessons import sort_lessons
from yomitan import yomitan

DEFAULT_OUT_PATH = "downloads"
DEFAULT_OUT_WORDS_PATH = os.path.join(DEFAULT_OUT_PATH, "lingqs")
DEFAULT_FROM_LESSON = 1
DEFAULT_TO_LESSON = 100
DEFAULT_AUDIOS_FOLDER = None


@click.group()
@click.version_option()
def cli():
    """Lingq command line scripts.

    You can always get more details about a command with the --help flag.
    """


@cli.command("setup")
@click.argument("apikey")
def setup_cli(apikey: str) -> None:
    """Creates or updates an .env file with your LingQ API key.

    You can find you key here: https://www.lingq.com/accounts/apikey/
    """
    env_file = ".env"

    if os.path.exists(env_file):
        with open(env_file, "r") as file:
            lines = file.readlines()

        # Update the API_KEY if it exists, otherwise add a new line
        with open(env_file, "w") as file:
            api_key_found = False
            for line in lines:
                if line.startswith("APIKEY="):
                    file.write(f"APIKEY={apikey}\n")
                    api_key_found = True
                else:
                    file.write(line)

            if not api_key_found:
                file.write(f"APIKEY={apikey}\n")

        print(f".env file has been updated.")
    else:
        with open(env_file, "w") as file:
            file.write(f"APIKEY={apikey}\n")

        print(f".env file has been created.")


@cli.command("fix")
@click.argument("language_code")
@click.argument("course_id")
def fix_cli(language_code: str, course_id: str) -> None:
    """Fix text for a course.

    Only supports ja and el at the moment, even though it should work for every language.
    """
    from fix import fix

    fix(language_code, course_id)


@cli.group()
def show():
    """Show commands."""


@show.command("my")
@click.argument("language_code")
def show_my_cli(language_code: str) -> None:
    """Show a list with my collections in the given language."""
    show_my(language_code)


@cli.group()
def get():
    """Get commands."""


@get.command("pictures")
@click.argument("language_code")
@click.argument("course_id")
@click.option("--out", "-o", default=DEFAULT_OUT_PATH, show_default=True, help="Output path.")
def get_pictures_cli(language_code: str, course_id: str, out: str) -> None:
    """Get pictures."""
    get_pictures(language_code, course_id, out)


@get.command("words")
@click.argument("language-codes", nargs=-1)
@click.option(
    "--out",
    "-o",
    default=DEFAULT_OUT_WORDS_PATH,
    show_default=True,
    help="Output path.",
)
def get_words_cli(language_codes: list[str], out: str) -> None:
    """Get words (LingQs)."""
    get_words(language_codes, out)


@cli.command("yomitan")
@click.argument("language-codes", nargs=-1)
@click.option(
    "--input",
    "-i",
    default=DEFAULT_OUT_WORDS_PATH,
    show_default=True,
    help="Input path to the JSON dump.",
)
def yomitan_cli(language_codes: list[str], input: str) -> None:
    """
    Make a Yomitan dictionary from a LingQ JSON dump generated through get_words.

    If no language codes are given, use all languages.
    """
    yomitan(language_codes, input)


@get.command("lessons")
@click.argument("language_code")
@click.argument("course_id")
@click.option("--skip_already_downloaded", is_flag=True, default=False, show_default=True)
@click.option("--download_audio", is_flag=True, default=False, help="If set, also download audio.")
@click.option(
    "--download_timestamps", is_flag=True, default=False, help="If set, also download timestamps."
)
@click.option("--out", "-o", default=DEFAULT_OUT_PATH, show_default=True, help="Output path.")
def get_lessons_cli(
    language_code: str,
    course_id: str,
    skip_already_downloaded: bool,
    download_audio: bool,
    download_timestamps: bool,
    out: str,
) -> None:
    """Get every lesson from a course id.

    CAREFUL: This reorders your 'Continue studying' shelf.
    """
    get_lessons(
        language_code,
        course_id,
        skip_already_downloaded,
        download_audio,
        download_timestamps,
        out,
        write=True,
        verbose=True,
    )


@get.command("courses")
@click.argument("language-codes", nargs=-1)
@click.option("--download-audio", is_flag=True, default=False, help="If set, also download audio.")
@click.option(
    "--download_timestamps", is_flag=True, default=False, help="If set, also download timestamps."
)
@click.option(
    "--sleep-time", type=int, default=2, show_default=True, help="Time to wait between courses."
)
@click.option("--out", "-o", default=DEFAULT_OUT_PATH, show_default=True, help="Output path.")
def get_courses_cli(
    language_codes: list[str],
    download_audio: bool,
    download_timestamps: bool,
    sleep_time: int,
    out: str,
) -> None:
    """Get every course from a list of languages.

    CAREFUL: This reorders your 'Continue studying' shelf.

    If no language codes are given, use all languages.
    """
    get_courses(language_codes, download_audio, download_timestamps, sleep_time, out)


@cli.command("post")
@click.argument("language_code")
@click.argument("course_id")
@click.argument("texts_folder")
@click.option("-a", "--audios_folder", default=DEFAULT_AUDIOS_FOLDER)
@click.option("--fr_lesson", type=int, default=DEFAULT_FROM_LESSON)
@click.option("--to_lesson", type=int, default=DEFAULT_TO_LESSON)
@click.option(
    "--pairing_strategy",
    type=click.Choice(["zip", "match_exact_titles"]),
    default="match_exact_titles",
)
def post_cli(
    language_code: str,
    course_id: str,
    texts_folder: str,
    audios_folder: str | None,
    fr_lesson: int,
    to_lesson: int,
    pairing_strategy: str,
) -> None:
    """Post command."""
    post(
        language_code,
        course_id,
        texts_folder,
        audios_folder,
        fr_lesson,
        to_lesson,
        pairing_strategy,
    )


@cli.command("postyt")
@click.argument("language_code")
@click.argument("course_id")
@click.argument("playlist_url")
@click.option("--skip_uploaded", default=True)
@click.option("--download_audio", default=False)
@click.option("--skip_without_cc", default=False)
def post_yt_playlist_cli(
    language_code: str,
    course_id: str,
    playlist_url: str,
    skip_uploaded: bool,
    download_audio: bool,
    skip_without_cc: bool,
) -> None:
    """Post youtube playlist."""
    post_yt_playlist(
        language_code, course_id, playlist_url, skip_uploaded, download_audio, skip_without_cc
    )


@cli.group()
def patch():
    """Patch commands."""


@patch.command("audios")
@click.argument("language_code")
@click.argument("course_id")
@click.argument("audios_folder")
@click.option("--fr_lesson", type=int, default=DEFAULT_FROM_LESSON)
@click.option("--to_lesson", type=int, default=DEFAULT_TO_LESSON)
def patch_audios_cli(
    language_code: str, course_id: str, audios_folder: str, fr_lesson: int, to_lesson: int
) -> None:
    """Patch a course audio."""
    patch_audios(language_code, course_id, audios_folder, fr_lesson, to_lesson)


@patch.command("texts")
def patch_texts_cli():
    """Not implemented."""
    return NotImplementedError


@cli.command("resplit")
@click.argument("course_id")
def resplit_ja_cli(course_id: str) -> None:
    """Resplit a course (only for japanese)."""
    resplit(course_id)


@cli.command("markdown")
@click.argument("language-codes", nargs=-1)
@click.option(
    "--select_courses",
    default="all",
    show_default=True,
    type=click.Choice(["all", "mine", "shared"]),
    help="Select which courses to include.",
)
@click.option(
    "--include_views",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include the number of views in the markdown.",
)
@click.option("--out", "-o", default=DEFAULT_OUT_PATH, show_default=True, help="Output path.")
def markdown_cli(
    language_codes: list[str],
    select_courses: str,
    include_views: bool,
    out: str,
) -> None:
    """Generate markdown files for the given language codes.

    If no language codes are given, use all languages.
    """
    make_markdown(language_codes, select_courses, include_views, out)


@cli.command("timestamp")
@click.argument("language_code")
@click.argument("course_id")
@click.option("--skip_already_timestamped", default=True)
def generate_timestamps_cli(
    language_code: str, course_id: str, skip_already_timestamped: bool
) -> None:
    """Generate timestamps for a course."""
    generate_timestamps(language_code, course_id, skip_already_timestamped)


@cli.command("overview")
@click.argument("language_code")
def overview_cli(language_code: str) -> None:
    """Library overview."""
    overview(language_code)


@cli.command("sort")
@click.argument("language_code")
@click.argument("course_id")
def sort_lessons_cli(language_code: str, course_id: str) -> None:
    """Sort all lessons from a course."""
    sort_lessons(language_code, course_id)


if __name__ == "__main__":
    cli()
