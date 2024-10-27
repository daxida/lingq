"""
How to Import and Structure a Book

1. Obtain the text of the book:
   - Get a PDF file of the book.
   - Use a conversion tool like https://convertio.co/ to convert the PDF into a DOCX format.
     This conversion helps by merging sentences, removing line breaks, etc.
   - Open the DOCX file in a text editor and copy-paste the contents into a file named "book.txt".

2. Clean the text:
   - Manually remove unwanted sections at the beginning and end of the text
     (e.g., Prologue, editor’s notices, etc.).

3. Prepare Headings (Optional):
   This is the part that is completely text dependent.
   You may need to modify `main()` and `prepare_headings()` to adapt it to your case.

   - If the book has a Table of Contents, copy it into a separate file, "headings.txt".
   - With an example Table of Contents like this:
       Πρόλογος ......................... 8
       Α'. Έλληνες και Βούλγαροι ....... 10
       Β'. Σκλαβιά ..................... 16
     You have two choices in `prepare_headings()`:
         - Extract titles manually into a suitable python format and insert them in the code.
         - Extract titles with a custom regex.
   - NOTE1: The previous step assumes that you can associate some pattern to the title.
       For most cases the pattern will be the same as the title, but if the PDF contains
       typos, or conversion errors this does not need to be the case.
       Consider a title:
         - "1. The beginning" (found throught Table of Contents)
       that in the actual text was malformed as "he beginning".
       In this case you may want to taylor the pattern in `prepare_headings()`.
   - NOTE2: In pathological cases like:
         - There is no Table of Contents
         - The text is malformed to the point of not having titles
         - The separator actually covers multiple lines
       You can always manually add a separator, f.e. "$" (level1), "$$" (level2), and
       adapt the logic of the code.

If it succeeds, this script will output each section to a separate file in the "split" folder,
with files named according to their hierarchical structure.
"""

import re
import shutil
from pathlib import Path

FPATH = Path(__file__).parent
OUT_FOLDER = FPATH / "split"
IPATH = FPATH / "book.txt"
HEADINGS_PATH = FPATH / "headings.txt"  # Optional

SplitData = list[str] | dict[str, "SplitData"]
Heading = tuple[str, str]  # Title, then pattern
Headings = list[Heading]


def separate(text_lines: list[str], ranked_headings: list[Headings]) -> SplitData:
    if not any(ranked_headings):
        return text_lines

    cur_headings, *next_headings = ranked_headings
    depth_heading = 0
    cur_pattern = re.compile(cur_headings[depth_heading][1])

    split_data = {}
    cur_section = None
    cur_lines = []
    reached_end = False

    for line in text_lines:
        if not reached_end and cur_pattern.search(line):
            # If there's an active section, recursively process it
            if cur_section is not None:
                split_data[cur_section] = separate(cur_lines, next_headings)

            # Start a new section with the current heading
            # We could also use the lin here (but writing / testing may become tricky)
            cur_section = cur_headings[depth_heading][0]
            cur_lines = []

            # From now on, test against the next heading
            if depth_heading < len(cur_headings) - 1:
                depth_heading += 1
                cur_pattern = re.compile(cur_headings[depth_heading][1])
            else:
                reached_end = True
        else:
            cur_lines.append(line)

    # Add the last section after finishing the loop
    if cur_section is not None:
        split_data[cur_section] = separate(cur_lines, next_headings)
    # If no headings matched, return the lines as a list
    elif cur_lines:
        return cur_lines

    return split_data


def write_recursive(
    split_data: SplitData, ranked_headings: list[Headings], filetitles: list[tuple[int, str]] = []
) -> None:
    """Recursively write the structured data to files in the specified folder."""
    if isinstance(split_data, list):
        file_title = filetitles[-1][1]
        # With tree indices...
        # file_title = "_".join([str(idx) for idx, _ in file_titles] + [file_titles[-1][1]])
        filepath = OUT_FOLDER / f"{file_title}.txt"
        with filepath.open("w") as f:
            for line in split_data:
                f.write(line)
    else:
        for idx, (title, content) in enumerate(split_data.items(), 1):
            write_recursive(
                content,
                ranked_headings,
                filetitles=filetitles + [(idx, title)],
            )


def test_titles(split_data: SplitData, ranked_headings: list[Headings], level: int = 0) -> bool:
    """
    Tests that every chapter in the heading list is correctly found, recursively.
    Returns True if all the chapters are found.
    """
    if isinstance(split_data, list):
        return True
    else:
        indent = "  " * level
        ok = True
        for idx, (title, _) in enumerate(ranked_headings[level], 1):
            prefix = f"{indent}{idx:02d}. "
            if title in split_data:
                print(f"{prefix}{title}")
                ok &= test_titles(split_data[title], ranked_headings, level + 1)
            else:
                print(f"{prefix}{title} (NOT FOUND)")
                ok = False
        return ok


def duplicate(lsts: list[list[str]]) -> list[Headings]:
    """For we want the patterns to be the same as the titles."""
    return [[(x, x) for x in lst] for lst in lsts]


def prepare_headings() -> list[Headings]:
    """How to extract headings from the text."""
    harcode = False

    if harcode:
        _rh = [
            ["ΜΕΡΟΣ ΠΡΩΤΟ", "ΔΕΥΤΕΡΟ ΜΕΡΟΣ", "ΤΡΙΤΟ ΜΕΡΟΣ"],
            ["I", "II", "III", "IV", "V", "VI", "VII"],
        ]
        ranked_headings = duplicate(_rh)
        return ranked_headings
    else:
        lines = HEADINGS_PATH.open("r").readlines()

        # Regex to match a heading from a line
        re_heading = r"^(.+) \.\.\."
        headings = []
        for line in lines:
            if mtch := re.match(re_heading, line):
                title = mtch.group(1)
                pattern = r"\$"
                heading = (title, pattern)
                headings.append(heading)

        ranked_headings = [headings]
        # print(f"Found {len(headings)} headings")
        # print(ranked_headings)  # Use this to switch to hardcode
        return ranked_headings


def main() -> None:
    if OUT_FOLDER.exists():
        print(f"Deleting old files at: {OUT_FOLDER}")
        shutil.rmtree(OUT_FOLDER)
    Path.mkdir(OUT_FOLDER, parents=True, exist_ok=True)

    text = IPATH.open("r").read()
    # If the headings patterns are spread over multiple lines,
    # we have to fit them in a line or the separate logic will not work:
    text = re.sub(r" \n \n \n", "$", text)

    text_lines = text.splitlines(keepends=True)

    ranked_headings = prepare_headings()
    separated_data = separate(text_lines, ranked_headings)

    if test_titles(separated_data, ranked_headings):
        print("Found all chapters")

    write_recursive(separated_data, ranked_headings)


if __name__ == "__main__":
    main()
