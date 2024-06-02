import re


def create_headings(text_path: str) -> None:
    headings: list[str] = []
    with open(text_path, "r") as t:
        for line in t.readlines():
            # REPLACE here with the suitable heading pattern
            heading = re.findall(r"[XVI]+ .*[a-zA-Z]\n", line)
            if heading:
                headings.append(heading[0].strip())

    print(headings)
    print(f"There are {len(headings)} headings")


def main():
    text_path = "text.txt"
    create_headings(text_path)


if __name__ == "__main__":
    main()
