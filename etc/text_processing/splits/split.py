from pathlib import Path

OUT_FOLDER = Path("split")
IN_FILE = Path("norwegian_wood.txt")

# Headings folder. The expected format is a list of chapter (=headings) separators, f.e:
# Chapter 1
# Chapter 2
# etc
HEADINGS_FOLDER = Path("headings.txt")

SplitData = dict[str, list[str]]


def split_by_headings(lines: list[str], headings: list[str]) -> SplitData:
    """
    Returns a dictionary where:
    - A key is the name of a chapter (=heading)
    - A value is a list of strings each representing a line of the chapter
    """
    split_data: SplitData = {}
    buf = []
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
            assert heading is not None
            split_data[heading] = buf

    return split_data


def write(split_data: SplitData, headings: list[str]) -> None:
    """In case of not found chapters, it writes a ?? file for easier fixing"""
    for idx_p, heading in enumerate(headings, 1):
        if heading in split_data.keys():
            opath = OUT_FOLDER / f"{idx_p:02d}. {heading}.txt"
            with opath.open("w") as f:
                for line in split_data[heading]:
                    f.write(line)
        else:
            opath = OUT_FOLDER / f"{idx_p:02d}. ?????????.txt"
            with opath.open("w") as f:
                f.write("NONE")


def test_titles(split_data: SplitData, headings: list[str]) -> int:
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


def main() -> None:
    Path.mkdir(OUT_FOLDER, parents=True, exist_ok=True)

    # Delete the contents of OUT_FOLDER if any.
    print(f"Deleting old files (if any) at this path: {OUT_FOLDER}")
    for file in OUT_FOLDER.iterdir():
        if file.is_file():
            file.unlink()

    # Read the text from the given input folders.
    with HEADINGS_FOLDER.open("r") as f:
        # Ensure no trailing empty heading
        headings = [heading.strip() for heading in f.readlines()]
    with IN_FILE.open("r") as f:
        lines = f.readlines()

    split_data = split_by_headings(lines, headings)

    error_code = test_titles(split_data, headings)
    if error_code != 0:
        return

    write(split_data, headings)


if __name__ == "__main__":
    main()
