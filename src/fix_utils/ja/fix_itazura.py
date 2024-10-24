# Fixes some issues with itazura (vertical writing)

import re
from pathlib import Path

FOLDER_PATH = Path("src/かがみの孤城")


def fix_vertical_characters(text: str) -> str:
    trans_dict = {
        "︱": "ー",
        "︶": ")",
        "︵": "(",
        "﹁": "「",
        "﹂": "」",
        "﹃": "『",
        "﹄": "』",
    }

    translation_dict = {ord(k): ord(v) for k, v in trans_dict.items()}
    translation_table = str.maketrans(translation_dict)

    return text.translate(translation_table)


def fix_paragraph_jumps(text: str) -> str:
    # \n==\n is also a possible separator
    return re.sub(r"\n(\n)+(?!\n)", "\n--\n", text)


def specific_replacements(text: str) -> str:
    # These do not display properly in LingQ when re-splitting
    to_replace = {
        "「": "<",
        "」": ">",
    }
    for string, replacement in to_replace.items():
        text = text.replace(string, replacement)

    return text


def fix(text: str) -> str:
    text = fix_vertical_characters(text)
    text = specific_replacements(text)
    text = fix_paragraph_jumps(text)
    return text


def process_file(file_path: Path):
    with file_path.open("r") as file:
        text = file.read()
        text = fix(text)
    extension = ""  # Fill this with some string to not overwrite the original
    opath = file_path.with_stem(file_path.stem + extension)
    with opath.open("w") as out:
        out.write(text)


def main():
    for file_path in FOLDER_PATH.iterdir():
        process_file(file_path)


if __name__ == "__main__":
    main()
