from pathlib import Path

import click

from commands.fix import fix
from commands.generate_timestamps import generate_timestamps
from commands.get_courses import get_courses
from commands.get_lessons import get_lessons
from commands.get_pictures import get_pictures
from commands.get_words import get_words
from commands.library_overview import overview
from commands.make_markdown import make_markdown
from commands.patch import patch_audios
from commands.post import PAIRING_STRATEGIES, post
from commands.post_yt_playlist import post_yt_playlist
from commands.resplit import resplit
from commands.show import show_my
from commands.sort_lessons import sort_lessons
from commands.yomitan import yomitan

DEFAULT_OUT_PATH = Path("downloads")
DEFAULT_OUT_WORDS_PATH = DEFAULT_OUT_PATH / "lingqs"
DEFAULT_AUDIOS_FOLDER = None
DEFAULT_TEXTS_FOLDER = None


def opath_option():  # noqa: ANN201
    return click.option(
        "--opath",
        "-o",
        default=DEFAULT_OUT_PATH,
        show_default=True,
        type=click.Path(exists=True, path_type=Path),
        help="Output path.",
    )


@click.group()
@click.version_option()
def cli() -> None:
    """Lingq command line scripts.

    You can always get more details about a command with the --help flag.
    """


@cli.command("setup")
@click.argument("apikey")
def setup_cli(apikey: str) -> None:
    """Creates or updates an .env file with your LingQ API key.

    You can find you key here: https://www.lingq.com/accounts/apikey/
    """
    env_file = Path(".env")

    if env_file.exists():
        with env_file.open("r") as file:
            lines = file.readlines()

        # Update the API_KEY if it exists, otherwise add a new line
        with env_file.open("w") as file:
            api_key_found = False
            for line in lines:
                if line.startswith("APIKEY="):
                    file.write(f"APIKEY={apikey}\n")
                    api_key_found = True
                else:
                    file.write(line)

            if not api_key_found:
                file.write(f"APIKEY={apikey}\n")

        print(".env file has been updated.")
    else:
        with env_file.open("w") as file:
            file.write(f"APIKEY={apikey}\n")

        print(".env file has been created.")


@cli.command("fix")
@click.argument("language_code")
@click.argument("course_id")
def fix_cli(language_code: str, course_id: int) -> None:
    """Fix text for a course.

    Only supports ja and el at the moment, even though it should work for every language.
    """
    fix(language_code, course_id)


@cli.group()
def show() -> None:
    """Show commands."""


@show.command("my")
@click.argument("language_code")
@click.option("--shared-only", is_flag=True, default=False, show_default=True)
@click.option("--codes", is_flag=True, default=False, show_default=True)
def show_my_cli(language_code: str, shared_only: bool, codes: bool) -> None:
    """Show a list with my collections in the given language."""
    show_my(language_code, shared_only, codes)


@cli.group()
def get() -> None:
    """Get commands."""


@get.command("pictures")
@click.argument("language_code")
@click.argument("course_id")
@opath_option()
def get_pictures_cli(language_code: str, course_id: int, opath: Path) -> None:
    """Get pictures."""
    get_pictures(language_code, course_id, opath)


@get.command("words")
@click.argument("language_codes", nargs=-1)
@opath_option()
def get_words_cli(language_codes: list[str], opath: Path) -> None:
    """Get words (LingQs)."""
    get_words(language_codes, opath)


@cli.command("yomitan")
@click.argument("language_codes", nargs=-1)
@click.option(
    "--ipath",
    "-i",
    default=DEFAULT_OUT_WORDS_PATH,
    show_default=True,
    type=click.Path(exists=True, path_type=Path),
    help="Input path.",
)
def yomitan_cli(language_codes: list[str], ipath: Path) -> None:
    """
    Make a Yomitan dictionary from a dump generated by 'get_words'.

    If no language codes are given, use all languages.
    """
    yomitan(language_codes, ipath)


@get.command("lessons")
@click.argument("language_code")
@click.argument("course_id")
@click.option(
    "--skip-downloaded",
    "-s",
    is_flag=True,
    default=False,
    show_default=True,
    help="Skip already downloaded lessons.",
)
@click.option("--download_audio", is_flag=True, default=False, help="If set, also download audio.")
@click.option(
    "--download_timestamps", is_flag=True, default=False, help="If set, also download timestamps."
)
@opath_option()
def get_lessons_cli(
    language_code: str,
    course_id: int,
    skip_downloaded: bool,
    download_audio: bool,
    download_timestamps: bool,
    opath: Path,
) -> None:
    """Get every lesson from a course id.

    CAREFUL: This reorders your 'Continue studying' shelf.
    """
    get_lessons(
        language_code,
        course_id,
        skip_downloaded,
        download_audio,
        download_timestamps,
        opath,
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
    "--skip-downloaded",
    "-s",
    is_flag=True,
    default=False,
    show_default=True,
    help="Skip already downloaded lessons.",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=1,
    show_default=True,
    help="Number of courses to download simultanously. Increasing this too much may incur in throttling. Suggested: 1 or 2.",
)
@opath_option()
def get_courses_cli(
    language_codes: list[str],
    opath: Path,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: int,
    batch_size: int,
) -> None:
    """Get every course from a list of languages.

    CAREFUL: This reorders your 'Continue studying' shelf.

    If no language codes are given, use all languages.
    """
    get_courses(
        language_codes,
        opath,
        download_audio=download_audio,
        download_timestamps=download_timestamps,
        skip_downloaded=skip_downloaded,
        batch_size=batch_size,
    )


@cli.command("post")
@click.argument("language_code")
@click.argument("course_id")
@click.option(
    "--texts-folder",
    "-t",
    default=DEFAULT_TEXTS_FOLDER,
    type=click.Path(exists=True, path_type=Path),
    help="Texts folder path.",
)
@click.option(
    "--audios-folder",
    "-a",
    default=DEFAULT_AUDIOS_FOLDER,
    type=click.Path(exists=True, path_type=Path),
    help="Audios folder path.",
)
@click.option(
    "--pairing-strategy",
    type=click.Choice(PAIRING_STRATEGIES),
    default="fuzzy",
    show_default=True,
)
def post_cli(
    language_code: str,
    course_id: int,
    texts_folder: Path | None,
    audios_folder: Path | None,
    pairing_strategy: str,
) -> None:
    """Upload lessons.

    When no texts are given, LingQ will use whisper to transcribe.
    """
    post(
        language_code,
        course_id,
        texts_folder,
        audios_folder,
        pairing_strategy,
    )


@cli.command("postyt")
@click.argument("language_code")
@click.argument("course_id")
@click.argument("playlist_url")
@click.option("--skip-uploaded", default=True, show_default=True)
def post_yt_playlist_cli(
    language_code: str,
    course_id: int,
    playlist_url: str,
    skip_uploaded: bool,
) -> None:
    """Post a youtube playlist."""
    post_yt_playlist(
        language_code,
        course_id,
        playlist_url,
        skip_uploaded=skip_uploaded,
        skip_no_cc=True,
    )


@cli.group()
def patch() -> None:
    """Patch commands."""


@patch.command("audios")
@click.argument("language_code")
@click.argument("course_id")
@click.option(
    "--audios-folder",
    "-a",
    default=DEFAULT_AUDIOS_FOLDER,
    type=click.Path(exists=True, path_type=Path),
    help="Audios folder path.",
)
def patch_audios_cli(language_code: str, course_id: int, audios_folder: str) -> None:
    """Patch a course audio."""
    patch_audios(language_code, course_id, audios_folder)


@patch.command("texts")
def patch_texts_cli() -> None:
    """Not implemented."""
    raise NotImplementedError()


@cli.command("resplit")
@click.argument("course_id")
def resplit_ja_cli(course_id: int) -> None:
    """Resplit a course (only for japanese)."""
    resplit(course_id)


@cli.command("markdown")
@click.argument("language-codes", nargs=-1)
@click.option(
    "--select-courses",
    default="all",
    show_default=True,
    type=click.Choice(["all", "mine", "shared"]),
    help="Select which courses to include.",
)
@click.option(
    "--include-views",
    is_flag=True,
    default=False,
    show_default=True,
    help="Include the number of views in the markdown.",
)
@opath_option()
def markdown_cli(
    language_codes: list[str],
    select_courses: str,
    include_views: bool,
    opath: Path,
) -> None:
    """Generate markdown files for the given language codes.

    If no language codes are given, use all languages.
    """
    make_markdown(language_codes, select_courses, include_views, opath)


@cli.command("timestamp")
@click.argument("language_code")
@click.argument("course_id")
@click.option("--skip-timestamped", default=True)
def generate_timestamps_cli(language_code: str, course_id: int, skip_timestamped: bool) -> None:
    """Generate timestamps for a course."""
    generate_timestamps(language_code, course_id, skip_timestamped)


@cli.command("overview")
@click.argument("language_code")
def overview_cli(language_code: str) -> None:
    """Library overview."""
    overview(language_code)


@cli.command("sort")
@click.argument("language_code")
@click.argument("course_id")
def sort_lessons_cli(language_code: str, course_id: int) -> None:
    """Sort all lessons from a course."""
    sort_lessons(language_code, course_id)


if __name__ == "__main__":
    cli()
