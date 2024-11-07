import asyncio
from datetime import datetime
from pathlib import Path

from lingqhandler import LingqHandler
from models.collection import Collection
from models.collection_v3 import SearchCollectionResult
from models.my_collections import CollectionItem
from utils import Colors, double_check, timing


def sanitize_title(title: str) -> str:
    return title.replace("|", "-").replace("[", "(").replace("]", ")")


def write_readme(language_codes: list[str], out_folder: Path) -> None:
    """
    Writes an index-like README.md:
        * [Greek (el)](./courses/courses_el.md)
        * [English (en)](./courses/courses_en.md)
        * [French (fr)](./courses/courses_fr.md)
        etc.
    """

    readme_path = out_folder / "README.md"
    with readme_path.open("w", encoding="utf-8") as f:
        for language_code in language_codes:
            f.write(f"* [{language_code}](./courses/courses_{language_code}.md)\n")


def format_markdown(collection_list: list[Collection], include_views: bool) -> str:
    """Convert a list of Collection objects to markdown format."""
    # Header
    fixing_date_width = "&nbsp;" * 6  # Ugly but works
    columns = [
        "Status",
        " ",
        "Title",
        "Views" if include_views else "",
        "Lessons",
        f"Created{fixing_date_width}",
        f"Updated{fixing_date_width}",
    ]
    header = "|".join(columns)
    header = header.replace("||", "|")
    n_columns = len(columns) if include_views else len(columns) - 1
    separator = "|".join(["-"] * n_columns)

    # Start building the markdown content
    markdown_lines = []
    markdown_lines.append(f"|{header}|\n")
    markdown_lines.append(f"|{separator}|\n")

    # Process each collection
    for c in collection_list:
        view_count = "-" if not c.views_count else c.views_count
        is_shared = "shared" if c.is_shared else "private"
        assert c.title is not None
        sanitized_title = sanitize_title(c.title)
        line_elements = [
            is_shared,
            c.level,
            f"[{sanitized_title}]({c.course_url})",
            view_count if include_views else "",
            c.amount_lessons,
            c.first_update,
            c.last_update,
        ]
        line = "|" + "|".join(map(str, line_elements)) + "\n"
        line = line.replace("||", "|")
        markdown_lines.append(line)

    return "".join(markdown_lines)


def write_markdown(
    collection_list: list[Collection], out_folder_markdown: Path, include_views: bool
) -> None:
    with out_folder_markdown.open("w", encoding="utf-8") as f:
        markdown = format_markdown(collection_list, include_views)
        f.write(markdown)


async def get_collections(handler: LingqHandler, select_courses: str) -> list[Collection]:
    """
    A collection is just a course in the web lingo.
    Given a language code, returns a list of Collection objects.
    Those store the important information of the JSON to then make the markdown.
    """

    collections_json: list[CollectionItem] | list[SearchCollectionResult]
    if select_courses == "all":
        collections_json = await handler.get_currently_studying_collections()
    else:
        _collections_json = await handler.get_my_collections()
        collections_json = _collections_json.results

    collections_list: list[Collection] = []
    n_collections = len(collections_json)

    tasks = [
        handler.get_collection_object_from_id(collection.id) for collection in collections_json
    ]
    collections = await asyncio.gather(*tasks)
    collections = [collection for collection in collections if collection is not None]

    for idx, col in enumerate(collections, 1):
        # To not mess with the sorting later on. This only happens in very weird cases.
        if col.last_update is None:
            print(
                f"[{idx}/{n_collections}] {Colors.SKIP}SKIP{Colors.END} {col.title} (last_update=None)"
            )
            continue

        # Ignore private collection if the shared_only flag is true
        if select_courses == "shared" and not col.is_shared:
            print(f"[{idx}/{n_collections}] {Colors.SKIP}SKIP{Colors.END} {col.title} (NOT SHARED)")
            continue

        print(f"[{idx}/{n_collections}] {Colors.OK}OK{Colors.END} {col.title}")

        collections_list.append(col)

    return collections_list


def sort_collections(collections: list[Collection]) -> None:
    # Sorts by descending date
    assert all(x.last_update is not None for x in collections)
    collections.sort(key=lambda x: datetime.strptime(x.last_update, "%Y-%m-%d"), reverse=True)  # type: ignore


async def make_markdown_async(
    language_codes: list[str],
    select_courses: str,
    include_views: bool,
    out_folder: Path,
) -> None:
    print(f"Making markdown for language(s): '{', '.join(language_codes)}'")
    print(f"With courses selection: {select_courses}")
    print(f"With include views: {include_views}")
    print(f"At folder: {out_folder}")
    double_check()

    extension_msg = "_no_views" if not include_views else ""
    readme_folder = out_folder / "markdowns" / f"markdown_{select_courses}{extension_msg}"
    courses_folder = readme_folder / "courses"
    Path.mkdir(courses_folder, parents=True, exist_ok=True)
    write_readme(language_codes, readme_folder)

    async with LingqHandler("Filler") as handler:
        n_languages = len(language_codes)
        for idx, language_code in enumerate(language_codes, 1):
            print(f"Starting download for {language_code} ({idx} of {n_languages})")

            handler.language_code = language_code
            collections_list = await get_collections(handler, select_courses)

            if not collections_list:
                print(f"Didn't find any courses for language: {language_code}")
                continue

            sort_collections(collections_list)

            out_folder_markdown = courses_folder / f"courses_{language_code}.md"
            write_markdown(collections_list, out_folder_markdown, include_views)
            print(f"Created markdown for {language_code}!")


@timing
def make_markdown(
    language_codes: list[str],
    select_courses: str,
    include_views: bool,
    out_folder: Path,
) -> None:
    """
    Generate markdown files for the given language codes.

    Args:
        language_codes (list[str]): List of language codes to process.
            If no language codes are given, use all languages.
        select_courses (str): Determines which courses to include.
            - "shared" for only my imported and shared collections (ignore private)
            - "mine"   for only my imported collections
            - "all"    for everything in the "Continue Studying" shelf
        include_views (bool): If True, includes the number of views in the markdown.
        out_folder (str): The output folder where the markdown files will be saved.
    """
    if not language_codes:
        language_codes = LingqHandler.get_user_language_codes()
    asyncio.run(make_markdown_async(language_codes, select_courses, include_views, out_folder))


if __name__ == "__main__":
    # Defaults for manually running this script.
    make_markdown(
        language_codes=["fr"],
        select_courses="all",  # all, shared or mine
        include_views=False,
        out_folder=Path("downloads"),
    )

    # Do everything:
    # for select_courses in ("all", "shared", "mine"):
    #     for include_views in (True, False):
    #         make_markdown([], select_courses, include_views, Path("downloads"))
