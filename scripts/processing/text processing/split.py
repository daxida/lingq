import os
from typing import List, Dict

OUT_FOLDER = "split"
IN_FILE = "norwegian_wood.txt"

# Headings folder. The expected format is a list of chapter (=headings) separators, f.e:
# Chapter 1
# Chapter 2
# etc
HEADINGS_FOLDER = "headings.txt"


def split_by_headings(lines: List[str], headings: List[str]) -> Dict:
    """
    Returns a dictionary where:
    - A key is the name of a chapter (=heading)
    - A value is a list of strings each representing a line of the chapter
    """
    split_data = dict()
    buf = list()
    heading = None
    amt_lines = len(lines)

    for idx, line in enumerate(lines):
        if line.strip() in headings:
            if heading and buf:
                split_data[heading] = buf
            heading = line.strip()
            buf = []
        else:
            buf.append(line)

        # Dump buffer at the end of input.
        if idx + 1 == amt_lines and buf:
            split_data[heading] = buf

    return split_data


def write(split_data: Dict, headings: List[str]) -> None:
    """In case of not found chapters, it writes a ?? file for easier fixing"""
    for idx_p, heading in enumerate(headings, 1):
        prefix = f"{OUT_FOLDER}/{idx_p:02d}. "

        if heading in split_data.keys():
            with open(f"{prefix}{heading}.txt", "w") as f:
                for line in split_data[heading]:
                    f.write(line)
        else:
            with open(f"{prefix}?????????.txt", "w") as f:
                f.write("NONE")


def test_titles(split_data: Dict, headings: List[str]) -> int:
    """Tests that every chapter in the heading list is correctly found"""
    print(f"{len(split_data)} chapters were found:")

    for idx, heading in enumerate(headings, 1):
        prefix = f"\t{idx:02d}. "

        if heading in split_data:
            print(f"{prefix}{heading}")
        else:
            print(f"{prefix}NOT FOUND")

    if len(split_data) == len(headings):
        print("Found every chapter!")
        return 0
    else:
        print("The following chapters couldn't be found:")
        for idx, heading in enumerate(headings, 1):
            if heading not in split_data:
                print(f"\t{idx:02d}. {heading}")
        return 1


def main():
    # Create OUT_FOLDER if it doesn't exist.
    if not os.path.exists(OUT_FOLDER):
        os.mkdir(OUT_FOLDER)

    # Delete the contents of OUT_FOLDER if any.
    print(f"Deleting old files (if any) at this path: {OUT_FOLDER}")
    for file_name in os.listdir(OUT_FOLDER):
        file = f"{OUT_FOLDER}/{file_name}"
        if os.path.isfile(file):
            os.remove(file)

    # Read the text from the given input folders.
    with open(HEADINGS_FOLDER, "r") as f:
        # Ensure no trailing empty heading
        headings = [heading.strip() for heading in f.readlines()]
    with open(IN_FILE, "r") as f:
        lines = f.readlines()

    split_data = split_by_headings(lines, headings)

    error_code = test_titles(split_data, headings)
    if error_code != 0:
        return

    write(split_data, headings)


if __name__ == "__main__":
    main()
