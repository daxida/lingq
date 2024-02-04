import re

filename = "18. Η επιβράβευση του Ντόμπι.txt"

# TODO
# - add remaining ambiguous capital letters


def upper(pat):
    return pat.group(1).upper()


def capitalize(pat):
    return pat.group(1).capitalize()


def fixProblematicChars(text: str) -> str:
    """
    Fixes:
       1. μ (mathematics and greek), τ
       2. Capital letters (capital alpha != capital a)
    """
    # TO TEST
    # Fixes mathematical mu
    text = re.sub(r"µ", "μ", text)

    # Fixes capital letters
    # Capital a -> capital alpha
    text = re.sub(r"A(?=[Ά-Ͽ]+)", r"Α", text)
    # Capital h -> capital ita
    text = re.sub(r"H(?=[Ά-Ͽ]+)", r"Η", text)

    return text


def specificFixes(text: str) -> str:
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

    # Specific replacements
    to_replace = {
        "Γιά": "Για",
        "ΡοΝ": "Ρον",
        "Τζινι": "Τζίνι",
        "πρι6έτ": "Πριβέτ",
        "μπέίκον": "μπέικον",
        "μακΓκόναγκαλ": "ΜακΓκόναγκαλ",
        "σχεδόνακέφαλος-Νικ": "Σχεδόν Ακέφαλος Νικ",
        "σχεδόν-ακέφαλοΝικ": "Σχεδόν Ακέφαλο Νικ",
        "σχεδόνακέφαλο-Νικ": "Σχεδόν Ακέφαλο Νικ",
        "σχεδόνακέ-φαλουΝικ": "Σχεδόν Ακέφαλου Νικ",
        "Tzacmv": "Τζάστιν",
        "Tzaonv": "Τζάστιν",
        "Tzacxiv": "Τζάστιν",
        "TZOOTIV": "Τζάστιν",
        "Τζασnv": "Τζάστιν",
        "ΦιντςΦλέτσλι": "Φιντς-Φλέτσλι",
        "κέίκ": "κέικ",
        "τσάί": "τσάι",
        "μακμίλαν": "ΜακΜίλαν",
    }
    for string, replacement in to_replace.items():
        text = text.replace(string, replacement)

    # Specific capitalizations
    # fmt: off
    to_capitalize = [
        # names
        "χάρι", "πότερ",
        "ρον", "ουέσλι",
        "ερμιόνη", "γκρέιντζερ",
        "ντράκο", "μαλφόι",
        "τζόρνταν",
        "σίμους", "μίλιγκαν",
        "παρβάτι", "πάτιλ",
        "λάβεντερ", "μπράουν",
        "άλμπους", "ντάμπλντορ",
        "βέρνον", "πετούνια",
        "άρθουρ", "μόλι", 
        "μπίλι",
        "πέρσι", # careful, πέρσι without caps also makes sense
        "σκάμπερς",
        "μινέρβα",  
        "σέβερους", "σνέιπ",
        "σπράουτ",
        "μπινς", "πινς",
        "πόμφρι",
        "σαλαζάρ",
        "γκρίφιντορ", "σλίθεριν", "χάφλπαφλ", "ράβενκλοου",
        "άργκους", "φιλτς", "πιβς",
        "μυρτιά", "μυρτιάς",
        "μπάροου",
        # others
        "αραγκόγκ",
        "πριβέτ",
        "αζκαμπάν",
        "σμέλτινγκς",
        "μαγκλ", "σκουίμπ",
        "κουίντιτς",
    ]
    # fmt: on
    for string in to_capitalize:
        # We don't want to sub subwords: Κληρονόμου -> ΚληΡονόμου
        text = re.sub(rf"({string}[^Ά-Ͽ])", capitalize, text)

    return text


def fixTextString(text: str) -> str:
    """Apply the fixes to the whole string of text"""

    # Fix page numbers
    text = re.sub(r"\d+\n", "", text)

    # Fix newlines
    text = re.sub(r"(?<=[^.;:?!\-\"\d\n])\n", " ", text)
    # Special case for newlines - due to splitting words
    text = re.sub(r"(?<=-)\n", "", text)
    # Fix double newlines
    text = re.sub(r"\n\n", "\n", text)

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


def fixTextLines(line: str) -> str:
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


def main():
    with open(filename, "r") as file:
        text = file.read()
        text = fixProblematicChars(text)
        text = specificFixes(text)

        text = fixTextString(text)
        text = specificFixes(text)

        text = "\n".join([fixTextLines(line) for line in text.split("\n")])
        text = specificFixes(text)

    write(filename, text)


if __name__ == "__main__":
    main()
