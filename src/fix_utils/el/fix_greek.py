import re
from typing import Match

# TODO: Make a test every time I use this script to fix a book.

filename = "18. Η επιβράβευση του Ντόμπι.txt"


def upper(pat: Match[str]) -> str:
    return pat.group(1).upper()


def capitalize(pat: Match[str]) -> str:
    return pat.group(1).capitalize()


def fix_problematic_chars(text: str) -> str:
    # Fixes mathematical mu
    text = re.sub(r"µ", "μ", text)

    return text


def is_english(word: str) -> bool:
    return all(ord(ch) < 200 for ch in word)


def fix_latin_letters(text: str) -> str:
    """Fix latin letters inserted into greek words."""

    # ABCDEFGHIJKLMNOPQRSTUVWXYZ
    # ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ

    # AMBIGUOUS ONES:
    # AΆBEÉHIÍKMNOÓPTXY

    # fmt: off
    latin_to_greek_upper = {
        "A": "Α", "Á": "Ά",
        "B": "Β",
        "E": "Ε", "É": "Έ",
        "H": "Η",
        "I": "Ι", "Í": "Ί",
        "K": "Κ",
        "M": "Μ",
        "N": "Ν",
        "O": "Ο", "Ó": "Ό",
        "P": "Ρ",
        "T": "Τ",
        "X": "Χ",
        "Y": "Υ",
    }
    latin_to_greek_lower = {
        "o": "ο", "ó": "ό",
        "u": "υ",
        "v": "ν",
    }
    # fmt: on

    latin_to_greek = {**latin_to_greek_upper, **latin_to_greek_lower}
    latin_symbols_concerned = "".join(latin_to_greek.keys())

    fixed_words: list[str] = []
    for word in text.split(" "):
        # If the word contains only latin letters, do not change it.
        if is_english(word):
            fixed_word = word
        else:
            fixed_word = re.sub(
                rf"[{latin_symbols_concerned}]",
                lambda m: latin_to_greek[m.group(0)],
                word,
            )
        fixed_words.append(fixed_word)

    return " ".join(fixed_words)


def specific_deletions(text: str) -> str:
    # Specific deletions
    # Add here the specific to the text deletions.
    to_remove = [
        "Created with novaPDF Printer (www.novaPDF.com). Please register to remove this message.",
        "-| ",
    ]
    for string in to_remove:
        text = text.replace(string, "")
    # Specific deletions (regex)
    text = re.sub(r"\|", " ", text)
    text = re.sub(r"'(?=Ό)", "", text)
    text = re.sub(r"'(?=Έ)", "", text)

    return text


def specific_replacements(text: str) -> str:
    # Specific replacements
    to_replace = {
        "Γιά": "Για",
    }
    for string, replacement in to_replace.items():
        text = text.replace(string, replacement)

    return text


def specific_capitalizations(text: str) -> str:
    # Specific capitalizations
    to_capitalize = [
        # names
        "χάρι",
        "πότερ",
        "ελλάδα",
        "Ελλάδα",
    ]
    for string in to_capitalize:
        # We don't want to sub subwords: Κληρονόμου -> ΚληΡονόμου
        text = re.sub(rf"({string}[^Ά-Ͽ])", capitalize, text)

    return text


def specific_fixes(text: str) -> str:
    text = specific_deletions(text)
    text = specific_replacements(text)
    text = specific_capitalizations(text)

    return text


def fix_textstring(text: str) -> str:
    """Apply the fixes to the whole string of text"""

    # Fix page numbers
    text = re.sub(r"\d+\n", "", text)

    # Fix newlines
    text = re.sub(r"(?<=[^.;:?!\-\"\d\n])\n", " ", text)
    # Special case for newlines - due to splitting words
    text = re.sub(r"(?<=-)\n", "", text)
    # Fix multiple newlines
    text = re.sub(r"\n{2,}}", "\n", text)

    # Fix multiple spaces
    text = re.sub(r" {2,}", " ", text)
    # Fix extra spaces before "
    text = re.sub(r" +(?=\"[ \n])", "", text)

    # Fix - splitting words (GREEK)
    text = re.sub(r"([Ά-Ͽ]+)\-([Ά-Ͽ]+)", r"\1\2", text)

    # Adds spaces after ponctuation if missing
    text = re.sub(r",(?=[^ ])", ", ", text)
    # We have to be careful of not changing ... -> . . .
    text = re.sub(r'\.(?=[^ ."])', ". ", text)
    text = re.sub(r';(?=[^ "])', "; ", text)
    # text = re.sub(r'»(?=[^ ])',  '» ', text)

    # Fix capital letters in the middle of a sentence.
    text = re.sub(r"(?<=[\.!;] )(.)", upper, text)
    text = re.sub(r"(?<=[\.!;] \")(.)", upper, text)

    return text


def fix_textlines(line: str) -> str:
    """Apply the fixes line by line"""

    # Removes starting spaces if any.
    line = re.sub(r"^ *", "", line)

    # Fix capital letters at the beggining of a sentence.
    line = re.sub(r"^(\"?.)", upper, line)

    # THIS FOR ONLY GREEK
    # line = re.sub(r'^"?([Α-Ωα-ωίϊΐόάέύϋΰήώ])', upper, line)
    # line = re.sub(r'^(\"?[Ά-Ͽ])', upper, line)

    return line


def write(filename: str, text: str):
    with open(f"fix_{filename}", "w") as out:
        for line in text.split("\n"):
            out.write(f"{line}\n")


def fix(text: str) -> str:
    text = fix_problematic_chars(text)
    text = fix_latin_letters(text)
    text = specific_fixes(text)

    text = fix_textstring(text)
    text = specific_fixes(text)

    text = "\n".join([fix_textlines(line) for line in text.split("\n")])
    text = specific_fixes(text)

    return text


def main():
    with open(filename, "r") as file:
        text = file.read()
        text = fix(text)

    write(filename, text)


if __name__ == "__main__":
    main()
