# Fixes some issues with itazura (vertical writing)

filename = "norwegian_wood.txt"


def fix_vertical_characters(text: str) -> str:
    text = text.replace("︱", "ー")
    text = text.replace("︶", ")")
    text = text.replace("︵", "(")
    text = text.replace("︵", "(")

    # These do not display properly in LingQ
    text = text.replace("﹁", "「")  # open
    text = text.replace("﹂", "」")  # close
    text = text.replace("﹃", "『")
    text = text.replace("﹄", "』")

    return text


def write(filename: str, text: str):
    with open(f"fix_{filename}", "w") as out:
        for line in text.split("\n"):
            out.write(f"{line}\n")


def main():
    with open(filename, "r") as file:
        text = file.read()
        text = fix_vertical_characters(text)

    write(filename, text)


if __name__ == "__main__":
    main()
