import os
from datetime import datetime

from utils import Collection, LingqHandler

# If True, creates a markdown for every language where we have known words.
# Otherwise set it to false and fill language_codes with the desired languages.
DOWNLOAD_ALL = False
LANGUAGE_CODES = ["fr"]

# "shared" for only my imported and shared collections (ignore private)
# "mine"   for only my imported
# "all"    for everything in the "Continue Studying" shelf
SELECT = "all"

# The folder name where we save the markdowns
OUT_FOLDER = f"markdown_{SELECT}"

# fmt: off
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[33m"
MAGENTA = "\033[35m"
RESET   = "\033[0m"
# fmt: on


def double_check():
    if input("Proceed? [y/n] ") != "y":
        print("Exiting")
        exit(1)


def create_README(language_codes):
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


def write_markdown(collection_list, language_code):
    out_path = f"{OUT_FOLDER}/courses/courses_{language_code}.md"
    with open(out_path, "w", encoding="utf-8") as md:
        # Headings
        fixing_date_width = "&nbsp;" * 6  # Ugly but works
        # fmt: off
        md.write(f"|Status| |Title|Views|Lessons|Created{fixing_date_width}|Updated{fixing_date_width}|\n")
        md.write("|------|-|-----|-----|-------|--------------|--------------|\n")
        # fmt: on

        for c in collection_list:
            c.viewsCount = "-" if not c.viewsCount else c.viewsCount
            is_shared = "shared" if c.is_shared else "private"
            # fmt: off
            md.write(f"|{is_shared}|{c.level}|[{c.title}]({c.course_url})|{c.viewsCount}|{c.amount_lessons}|{c.first_update}|{c.last_update}\n")
            # fmt: on


def get_collections(handler: LingqHandler, language_code: str):
    """
    A collection is just a course in the web lingo.
    Given a language code, returns a list of Collection objects.
    Those store the important information of the JSON to then make the markdown.
    """

    if SELECT == "all":
        collections = handler.get_currently_studying_collections(language_code)
    else:
        collections = handler.get_my_collections(language_code)

    collection_list = []
    n_collections = len(collections)

    for idx, my_collection in enumerate(collections, 1):
        _id = my_collection["id"]

        collection_v2 = handler.get_collection_from_id(language_code, _id)

        col = Collection()
        col.language_code = language_code
        col.add_data(collection_v2)

        # To not mess with the sorting later on. This only happens in very weird cases.
        if col.last_update is None:
            print(f"[{idx}/{n_collections}] {YELLOW}SKIP{RESET} {col.title} (last_update=None)")
            continue

        # Ignore private collection if the shared_only flag is true
        if SELECT == "shared" and not col.is_shared:
            print(f"[{idx}/{n_collections}] {YELLOW}SKIP{RESET} {col.title} (NOT SHARED)")
            continue

        print(f"[{idx}/{n_collections}] {GREEN}OK{RESET} {col.title}")

        collection_list.append(col)

    return collection_list


def sort_collections(collections) -> None:
    # Sorts by descending date
    collections.sort(key=lambda x: datetime.strptime(x.last_update, "%Y-%m-%d"), reverse=True)


def main(language_codes):
    handler = LingqHandler()

    if DOWNLOAD_ALL:
        language_codes = handler.get_language_codes()

    print(
        f"Making markdown for languages = {', '.join(language_codes)}",
        f"with select = {SELECT}",
    )
    double_check()

    if not os.path.exists(OUT_FOLDER):
        os.mkdir(OUT_FOLDER)

    courses_path = os.path.join(OUT_FOLDER, "courses")
    if not os.path.exists(courses_path):
        os.mkdir(courses_path)

    create_README(language_codes)

    n_languages = len(language_codes)
    for idx, language_code in enumerate(language_codes, 1):
        print(f"Starting download for {language_code} ({idx} of {n_languages})")

        collection_list = get_collections(handler, language_code)

        if not collection_list:
            print(f"Didn't find any courses for language: {language_code}")
            continue

        sort_collections(collection_list)
        write_markdown(collection_list, language_code)
        print(f"Created markdown for {language_code}!")


if __name__ == "__main__":
    main(LANGUAGE_CODES)
