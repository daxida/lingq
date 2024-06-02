import os

# Two level
Separated = dict[str, dict[str, list[str]]]


def clear_folder(path: str) -> None:
    for file_name in os.listdir(path):
        file = path + file_name
        if os.path.isfile(file):
            print("Deleting file:", file)
            os.remove(file)


def separate_by_heading(lines: list[str], heading_list: set[str]) -> dict[str, list[str]]:
    separated_data = {}
    buf = []
    heading = None
    lines_len = len(lines)

    for idx, line in enumerate(lines):
        if line.strip() in heading_list:
            if buf and heading:
                separated_data[heading] = buf
            heading = line.strip()
            buf = []
        else:
            buf.append(line)

        # Dump buffer at the end of input
        if idx + 1 == lines_len:
            if buf:
                separated_data[heading] = buf

    return separated_data


def separate(filename: str) -> Separated:
    # fmt: off
    h1 = {"ΜΕΡΟΣ ΠΡΩΤΟ", "ΔΕΥΤΕΡΟ ΜΕΡΟΣ", "ΤΡΙΤΟ ΜΕΡΟΣ", "ΤΕΤΑΡΤΟ ΜΕΡΟΣ"}
    h2 = {
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII",
        "IX", "Χ", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"
    }
    # fmt: on

    text_lines = open(filename, "r").readlines()

    separated_data = {}
    separated_data_h1 = separate_by_heading(text_lines, h1)

    for part in separated_data_h1:
        part_lines = separated_data_h1[part]
        separated_data_h2 = separate_by_heading(part_lines, h2)
        separated_data[part] = separated_data_h2

    return separated_data


def write(separated_data: Separated) -> None:
    for idx_p, part in enumerate(separated_data):
        chapters = separated_data[part]

        for idx_c, chapter in enumerate(chapters):
            if chapter:
                title = f"{idx_p + 1}.{idx_c + 1} {part} - {chapter.strip('.')}"
            else:
                title = f"{idx_p + 1} {part}"

            with open(f"split/{title}.txt", "w") as c:
                for line in chapters[chapter]:
                    c.write(line)


def test_titles(separated_data: Separated) -> None:
    print(f"There are {len(separated_data)} parts")
    for part in separated_data:
        print(f"There are {len(separated_data[part])} chapters in {part}")
        for chapter in separated_data[part]:
            print(part, chapter)


def main():
    folder_name = "split"
    os.makedirs(folder_name, exist_ok=True)

    path = f"/Users/rafa/Downloads/{folder_name}/"
    clear_folder(path)

    filename = "text.txt"
    separated_data = separate(filename)

    # test_titles(separated_data)

    write(separated_data)


if __name__ == "__main__":
    main()
