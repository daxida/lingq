# Fixes some issues with itazura (vertical writing)

import os

FOLDER_PATH = "src/かがみの孤城"


def fix_vertical_characters(text: str) -> str:
    trans_dict = {
        "︱": "ー",
        "︶": ")",
        "︵": "(",
        # These do not display properly in LingQ
        "﹁": "「",  # open
        "﹂": "」",  # close
        "﹃": "『",
        "﹄": "』",
    }

    trans_dict = {ord(k): ord(v) for k, v in trans_dict.items()}
    translation_table = str.maketrans(trans_dict)

    return text.translate(translation_table)


def fix_paragraph_jumps(text: str) -> str:
    return text.replace("\n\n", "\n--\n")


def fix(text: str) -> str:
    text = fix_vertical_characters(text)
    text = fix_paragraph_jumps(text)
    return text


def process_file(file_path: str):
    with open(file_path, "r") as file:
        text = file.read()
        text = fix(text)
    with open(f"{file_path}", "w") as out:
        out.write(text)


def main():
    for file_name in os.listdir(FOLDER_PATH):
        file_path = os.path.join(FOLDER_PATH, file_name)
        process_file(file_path)


if __name__ == "__main__":
    main()
