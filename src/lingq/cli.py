from pathlib import Path
from typing import Any, Callable, TypeVar

import click

from lingq.commands.add_timestamps import add_timestamps
from lingq.commands.get_courses import get_courses
from lingq.commands.get_images import get_images
from lingq.commands.get_lesson import get_lesson
from lingq.commands.get_lessons import get_lessons
from lingq.commands.get_words import get_words
from lingq.commands.merge import merge
from lingq.commands.mk_library_overview import overview
from lingq.commands.mk_markdown import markdown
from lingq.commands.mk_yomitan import YOMITAN_DICT_CHOICES, YomitanDictTy, yomitan
from lingq.commands.patch import patch_audios
from lingq.commands.post import PAIRING_STRATEGIES, Strategy, post
from lingq.commands.post_yt_playlist import post_yt_playlist
from lingq.commands.reindex import reindex
from lingq.commands.replace import replace
from lingq.commands.resplit import resplit
from lingq.commands.show import show_course, show_my, show_status
from lingq.commands.sort import sort_lessons
from lingq.commands.stats import stats
from lingq.config import CONFIG_DIR, CONFIG_PATH
from lingq.lingqhandler import LingqHandler

DEFAULT_OUT_PATH = Path("downloads")
DEFAULT_OUT_WORDS_PATH = DEFAULT_OUT_PATH / "lingqs"
DEFAULT_AUDIOS_FOLDER = None
DEFAULT_TEXTS_FOLDER = None


T = TypeVar("T", bound=Callable[..., Any])
"""Simple version of click.decorators.FC."""


def opath_option() -> Callable[[T], T]:
    return click.option(
        "--opath",
        "-o",
        default=DEFAULT_OUT_PATH,
        show_default=True,
        type=click.Path(path_type=Path),
        help="Output path.",
    )


def dry_run_option() -> Callable[[T], T]:
    return click.option(
        "--dry-run",
        "-n",
        is_flag=True,
        help="Show what would change without modifying anything.",
    )


def assume_yes_option() -> Callable[[T], T]:
    # Reference: https://linux.die.net/man/8/apt-get
    return click.option(
        "--yes",
        "-y",
        is_flag=True,
        help="Automatic yes to prompts.",
    )


class LangType(click.ParamType):
    """A helper class to do language code validation at CLI time.

    Uses a cache to prevent sending multiple requests when parsing a list of LangType.

    # When the command expects a list of LangType (nargs = -1)
    get courses        | None      | 'None' does not call convert (cf. docs)
    get courses el xxx | [el, xxx] | validates (request for 'el', then cache for xxx)

    # When the command expects a LangType
    show my            | None      | fails before validation
    show my ""         | ""        | validates
    show my el         | el        | validates
    """

    name = "language"

    def __init__(self) -> None:
        self._cache: list[str] | None = None

    def _get_lang_codes(self) -> list[str]:
        if self._cache is None:
            self._cache = LingqHandler.get_user_langs()
        return self._cache

    def convert(self, value: str, param, ctx) -> str:  # noqa: ANN001
        lang_codes = self._get_lang_codes()
        if value not in lang_codes:
            self.fail(
                f"{value}.\nLanguages found for this account: {', '.join(sorted(lang_codes))}.",
                param,
                ctx,
            )
        return value


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="lingq")
def cli() -> None:
    """Lingq command line scripts.

    See more details about a command with the --help flag.
    """


@cli.command("setup")
@click.argument("apikey")
def setup_cli(apikey: str) -> None:
    """Create or update a config file with your LingQ API key.

    You can find your API key at: https://www.lingq.com/accounts/apikey/
    """

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r") as file:
            lines = file.readlines()

        # Update the API_KEY if it exists, otherwise add a new line
        with CONFIG_PATH.open("w") as file:
            api_key_found = False
            for line in lines:
                if line.startswith("APIKEY="):
                    file.write(f"APIKEY={apikey}\n")
                    api_key_found = True
                else:
                    file.write(line)

            if not api_key_found:
                file.write(f"APIKEY={apikey}\n")

        print(f"Config file has been updated at {CONFIG_PATH}")
    else:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w") as file:
            file.write(f"APIKEY={apikey}\n")

        print(f"Config file has been created at {CONFIG_PATH}")


@cli.group()
def show() -> None:
    """Show commands."""


@show.command("my")
@click.argument("lang", type=LangType())
@click.option("-s", "--shared", is_flag=True, default=False, show_default=True)
@click.option("-c", "--codes", is_flag=True, default=False, show_default=True)
@click.option("-v", "--verbose", is_flag=True, default=False, show_default=True)
def show_my_cli(lang: str, shared: bool, codes: bool, verbose: bool) -> None:
    """Show my collections in a language."""
    show_my(lang, shared=shared, codes=codes, verbose=verbose)


@show.command("course")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@click.option("-s", "--shared", is_flag=True, default=False, show_default=True)
@click.option("-c", "--codes", is_flag=True, default=False, show_default=True)
@click.option("-v", "--verbose", is_flag=True, default=False, show_default=True)
def show_course_cli(
    lang: str,
    course_id: int,
    shared: bool,
    codes: bool,
    verbose: bool,
) -> None:
    """Show lessons in a language."""
    show_course(lang, course_id, shared=shared, codes=codes, verbose=verbose)


@show.command("status")
@click.argument("lang", type=LangType())
def show_status_cli(lang: str) -> None:
    """Show pending and refused lessons in a language."""
    show_status(lang)


@show.command("stats")
@click.argument("lang", type=LangType())
def stats_cli(lang: str) -> None:
    """Show stats."""
    stats(lang)


@cli.group()
def get() -> None:
    """Get commands."""


@get.command("images")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@opath_option()
def get_images_cli(lang: str, course_id: int, opath: Path) -> None:
    """Get course images."""
    get_images(lang, course_id, opath)


@get.command("words")
@click.argument("langs", nargs=-1, type=LangType())
@opath_option()
def get_words_cli(langs: list[str], opath: Path) -> None:
    """Get all words (LingQs) for the given languages.

    If no language codes are given, use all languages.
    """
    get_words(langs, opath)


@get.command("lesson")
@click.argument("lang", type=LangType())
@click.argument("lesson_id")
@opath_option()
@click.option("--download-audio", is_flag=True, default=False, help="Also download audio.")
@click.option(
    "--download-timestamps", is_flag=True, default=False, help="Also download timestamps."
)
def get_lesson_cli(
    lang: str,
    lesson_id: int,
    opath: Path,
    download_audio: bool,
    download_timestamps: bool,
) -> None:
    """Get a lesson from a lesson id.

    CAREFUL: This reorders your 'Continue studying' shelf.
    """
    get_lesson(
        lang,
        lesson_id,
        opath,
        download_audio=download_audio,
        download_timestamps=download_timestamps,
    )


@get.command("lessons")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@opath_option()
@click.option("--download-audio", is_flag=True, default=False, help="Also download audio.")
@click.option(
    "--download-timestamps", is_flag=True, default=False, help="Also download timestamps."
)
@click.option(
    "--skip-downloaded",
    "-s",
    is_flag=True,
    default=False,
    show_default=True,
    help="Skip already downloaded lessons.",
)
@click.option("--with-index", is_flag=True, default=False, help="Add index to the title.")
def get_lessons_cli(
    lang: str,
    course_id: int,
    opath: Path,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    with_index: bool,
) -> None:
    """Get all lessons from a course id.

    CAREFUL: This reorders your 'Continue studying' shelf.
    """
    get_lessons(
        lang,
        course_id,
        opath,
        download_audio=download_audio,
        download_timestamps=download_timestamps,
        skip_downloaded=skip_downloaded,
        write=True,
        with_index=with_index,
    )


@get.command("courses")
@click.argument("langs", nargs=-1, type=LangType())
@opath_option()
@click.option("--download-audio", is_flag=True, default=False, help="Also download audio.")
@click.option(
    "--download-timestamps", is_flag=True, default=False, help="Also download timestamps."
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
    help="Number of courses to download simultanously. "
    "Increasing this too much may incur in throttling. Suggested: 1 or 2.",
)
@assume_yes_option()
def get_courses_cli(
    langs: list[str],
    opath: Path,
    download_audio: bool,
    download_timestamps: bool,
    skip_downloaded: bool,
    batch_size: int,
    yes: bool,
) -> None:
    """Get all courses for the given languages.

    CAREFUL: This reorders your 'Continue studying' shelf.

    If no language codes are given, use all languages.
    """
    get_courses(
        langs,
        opath,
        download_audio=download_audio,
        download_timestamps=download_timestamps,
        skip_downloaded=skip_downloaded,
        batch_size=batch_size,
        assume_yes=yes,
    )


@cli.command("post")
@click.argument("lang", type=LangType())
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
    lang: str,
    course_id: int,
    texts_folder: Path,
    audios_folder: Path | None,
    pairing_strategy: Strategy,
) -> None:
    """Upload lessons.

    When no texts are given, LingQ will use whisper to transcribe.
    """
    post(
        lang,
        course_id,
        texts_folder,
        audios_folder,
        pairing_strategy,
    )


@cli.command("postyt")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@click.argument("playlist_url")
@click.option("--skip-uploaded", default=True, show_default=True)
def post_yt_playlist_cli(
    lang: str,
    course_id: int,
    playlist_url: str,
    skip_uploaded: bool,
) -> None:
    """Post a youtube playlist."""
    post_yt_playlist(
        lang,
        course_id,
        playlist_url,
        skip_uploaded=skip_uploaded,
        skip_no_cc=True,
    )


@cli.command("merge")
@click.argument("lang", type=LangType())
@click.argument("fr_course_id")
@click.argument("to_course_id")
def merge_cli(lang: str, fr_course_id: int, to_course_id: int) -> None:
    """Merge two courses.

    Moves all the lessons from course FR to course TO.

    The old course, even if it remains without any lessons, will not be deleted.
    """
    merge(lang, fr_course_id, to_course_id)


@cli.command("reindex")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@dry_run_option()
def reindex_cli(lang: str, course_id: int, dry_run: bool) -> None:
    """Reindex course titles."""
    reindex(lang, course_id, dry_run=dry_run)


@cli.group()
def patch() -> None:
    """Patch commands."""


@patch.command("audios")
@click.argument("langs", nargs=-1, type=LangType())
@click.argument("course_id")
@click.option(
    "--audios-folder",
    "-a",
    default=DEFAULT_AUDIOS_FOLDER,
    type=click.Path(exists=True, path_type=Path),
    help="Audios folder path.",
)
def patch_audios_cli(lang: str, course_id: int, audios_folder: Path) -> None:
    """Patch a course audio."""
    patch_audios(lang, course_id, audios_folder)


@cli.command("replace")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@click.argument("fr")
@click.argument("to")
@assume_yes_option()
def replace_cli(lang: str, course_id: int, fr: str, to: str, yes: bool) -> None:
    """Replace words in a course.

    Example (replace a with b): `lingq replace ja 123123 a b`
    """
    replacements = {fr: to}
    replace(lang, course_id, replacements, yes)


@cli.command("resplit")
@click.argument("lang", type=LangType())
@click.argument("course_id")
def resplit_cli(lang: str, course_id: int) -> None:
    """Resplit a course."""
    resplit(lang, course_id)


@cli.group()
def make() -> None:
    """Make commands."""


@make.command("overview")
@click.argument("lang", type=LangType())
def overview_cli(lang: str) -> None:
    """Make a library overview."""
    overview(lang)


@make.command("markdown")
@click.argument("langs", nargs=-1, type=LangType())
@opath_option()
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
def markdown_cli(
    langs: list[str],
    opath: Path,
    select_courses: str,
    include_views: bool,
) -> None:
    """Make markdown files for the given languages.

    If no language codes are given, use all languages.
    """
    markdown(langs, select_courses, include_views, opath)


@make.command("yomitan")
@click.argument("dict_ty", type=click.Choice(YOMITAN_DICT_CHOICES))
@click.argument("langs", nargs=-1, type=LangType())
@click.option(
    "--ipath",
    "-i",
    default=DEFAULT_OUT_WORDS_PATH,
    show_default=True,
    type=click.Path(exists=True, path_type=Path),
    help="Input path.",
)
def yomitan_cli(dict_ty: YomitanDictTy, langs: list[str], ipath: Path) -> None:
    """Make a Yomitan dictionary from the result of 'lingq get words'.

    If no language codes are given, use all languages.
    """
    yomitan(langs, ipath, dict_ty=dict_ty)


@cli.command("timestamp")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@click.option("--skip-timestamped", default=True)
def generate_timestamps_cli(lang: str, course_id: int, skip_timestamped: bool) -> None:
    """Add course timestamps."""
    add_timestamps(lang, course_id, skip_timestamped)


@cli.command("sort")
@click.argument("lang", type=LangType())
@click.argument("course_id")
@dry_run_option()
def sort_lessons_cli(lang: str, course_id: int, dry_run: bool) -> None:
    """Sort course lessons."""
    sort_lessons(lang, course_id, dry_run=dry_run)


if __name__ == "__main__":
    cli()
