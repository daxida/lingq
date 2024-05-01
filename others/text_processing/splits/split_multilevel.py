import os


def createFolderIfNotExist(folder_name):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)


def clearFolder(path):
    for file_name in os.listdir(path):
        file = path + file_name
        if os.path.isfile(file):
            print("Deleting file:", file)
            os.remove(file)


def separateByHeading(text, heading_list):
    separated_data = {}
    _buffer = []
    heading = None
    lines = len(text)

    for idx, line in enumerate(text):
        if line.strip() in heading_list:
            if _buffer and heading:
                separated_data[heading] = _buffer
            heading = line.strip()
            _buffer = []
        else:
            _buffer.append(line)

        # Dump buffer at the end of input
        if idx + 1 == lines:
            if _buffer:
                separated_data[heading] = _buffer

    return separated_data


def separate(filename):
    # fmt: off
    H1 = {"ΜΕΡΟΣ ΠΡΩΤΟ", "ΔΕΥΤΕΡΟ ΜΕΡΟΣ", "ΤΡΙΤΟ ΜΕΡΟΣ", "ΤΕΤΑΡΤΟ ΜΕΡΟΣ"}
    H2 = {
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", 
        "IX", "Χ", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"
    }
    # fmt: on

    text = open(filename, "r").readlines()

    separated_data = {}

    separated_data_H1 = separateByHeading(text, H1)

    for part in separated_data_H1:
        text_part = separated_data_H1[part]
        separated_data_H2 = separateByHeading(text_part, H2)

        separated_data[part] = separated_data_H2

    return separated_data


def write(separated_data):
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


def testTitles(separated_data):
    print(f"There are {len(separated_data)} parts")

    for part in separated_data:
        print(f"There are {len(separated_data[part])} chapters in {part}")

        for chapter in separated_data[part]:
            print(part, chapter)


def main():
    folder_name = "split"
    createFolderIfNotExist(folder_name)

    path = f"/Users/rafa/Downloads/{folder_name}/"
    clearFolder(path)

    filename = "text.txt"
    separated_data = separate(filename)

    # testTitles(separated_data)

    write(separated_data)


if __name__ == "__main__":
    main()
