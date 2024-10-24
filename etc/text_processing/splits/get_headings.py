import re
from pathlib import Path


def create_headings(filepath: Path) -> None:
    headings: list[str] = []
    with filepath.open("r") as t:
        for line in t.readlines():
            # REPLACE here with the suitable heading pattern
            heading = re.findall(r"[XVI]+ .*[a-zA-Z]\n", line)
            if heading:
                headings.append(heading[0].strip())

    print(headings)
    print(f"There are {len(headings)} headings")


def main():
    filename = "text.txt"
    filepath = Path(filename)
    create_headings(filepath)


if __name__ == "__main__":
    main()
