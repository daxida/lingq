import asyncio
import os
from datetime import datetime
from typing import List

from collection import Collection
from utils import LingqHandler, timing  # type: ignore

# If True, creates a markdown for every language where we have known words.
# Otherwise set it to false and fill language_codes with the desired languages.
DOWNLOAD_ALL = True
LANGUAGE_CODES = ["fr"]

# "shared" for only my imported and shared collections (ignore private)
# "mine"   for only my imported
# "all"    for everything in the "Continue Studying" shelf
SELECT_COURSES = "all"

# The folder name where we save the markdowns
OUT_FOLDER = f"markdowns/markdown_{SELECT_COURSES}"

# fmt: off
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[33m"
MAGENTA = "\033[35m"
RESET   = "\033[0m"
# fmt: on


def double_check() -> None:
    if input("Proceed? [y/n] ") != "y":
        print("Exiting")
        exit(1)


def create_README(language_codes: List[str]) -> None:
    """
    Returns a README markdown:
        * [Greek (el)](./courses/courses_el.md)
        * [English (en)](./courses/courses_en.md)
        * [French (fr)](./courses/courses_fr.md)
        etc.
    """

    with open(f"{OUT_FOLDER}/README.md", "w", encoding="utf-8") as f:
        for language_code in language_codes:
            f.write(f"* [{language_code}](./courses/courses_{language_code}.md)\n")


def write_markdown(collection_list: List[Collection], language_code: str) -> None:
    out_path = f"{OUT_FOLDER}/courses/courses_{language_code}.md"
    with open(out_path, "w", encoding="utf-8") as md:
        # Headings
        fixing_date_width = "&nbsp;" * 6  # Ugly but works
        # fmt: off
        md.write(f"|Status| |Title|Views|Lessons|Created{fixing_date_width}|Updated{fixing_date_width}|\n")
        md.write("|------|-|-----|-----|-------|--------------|--------------|\n")
        # fmt: on

        for c in collection_list:
            view_count = "-" if not c.viewsCount else c.viewsCount
            is_shared = "shared" if c.is_shared else "private"
            assert c.title is not None
            sanitized_title = c.title.replace("|", "-").replace("[", "(").replace("]", ")")
            line = f"|{is_shared}|{c.level}|[{sanitized_title}]({c.course_url})|{view_count}|{c.amount_lessons}|{c.first_update}|{c.last_update}\n"
            md.write(line)


async def get_collections(handler: LingqHandler) -> List[Collection]:
    """
    A collection is just a course in the web lingo.
    Given a language code, returns a list of Collection objects.
    Those store the important information of the JSON to then make the markdown.
    """

    if SELECT_COURSES == "all":
        collections_json = await handler.get_currently_studying_collections()
    else:
        collections_json = await handler.get_my_collections()

    collections_list: List[Collection] = []
    n_collections = len(collections_json)

    tasks = [
        handler.get_collection_object_from_id(collection["id"]) for collection in collections_json
    ]
    collections = await asyncio.gather(*tasks)

    for idx, col in enumerate(collections, 1):
        # To not mess with the sorting later on. This only happens in very weird cases.
        if col.last_update is None:
            print(f"[{idx}/{n_collections}] {YELLOW}SKIP{RESET} {col.title} (last_update=None)")
            continue

        # Ignore private collection if the shared_only flag is true
        if SELECT_COURSES == "shared" and not col.is_shared:
            print(f"[{idx}/{n_collections}] {YELLOW}SKIP{RESET} {col.title} (NOT SHARED)")
            continue

        print(f"[{idx}/{n_collections}] {GREEN}OK{RESET} {col.title}")

        collections_list.append(col)

    return collections_list


def sort_collections(collections: List[Collection]) -> None:
    # Sorts by descending date
    assert all(x.last_update is not None for x in collections)
    collections.sort(key=lambda x: datetime.strptime(x.last_update, "%Y-%m-%d"), reverse=True)  # type: ignore


async def make_markdown():
    async with LingqHandler("Filler") as handler:
        language_codes = LANGUAGE_CODES
        if DOWNLOAD_ALL:
            language_codes = await handler.get_language_codes()

        print(f"Making markdown for languages: '{', '.join(language_codes)}'")
        print(f"With courses selection: {SELECT_COURSES}")
        print(f"At folder: {OUT_FOLDER}")
        double_check()

        os.makedirs(os.path.join(OUT_FOLDER, "courses"), exist_ok=True)

        create_README(language_codes)

        n_languages = len(language_codes)
        for idx, language_code in enumerate(language_codes, 1):
            print(f"Starting download for {language_code} ({idx} of {n_languages})")

            handler.language_code = language_code
            collections_list = await get_collections(handler)

            if not collections_list:
                print(f"Didn't find any courses for language: {language_code}")
                continue

            sort_collections(collections_list)
            write_markdown(collections_list, language_code)
            print(f"Created markdown for {language_code}!")


@timing
def main():
    asyncio.run(make_markdown())


if __name__ == "__main__":
    main()
