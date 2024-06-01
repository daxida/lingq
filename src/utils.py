import os
import time
import unicodedata
from functools import wraps

from natsort import os_sorted


class colors:
    # fmt: off
    FAIL = "\033[31m"    # RED
    OK   = "\033[32m"    # GREEN
    WARN = "\033[33m"    # YELLOW
    SKIP = "\033[0;91m"  # ORANGE
    TIME = "\033[36m"    # CYAN
    END  = "\033[0m"
    # fmt: on


def double_check(msg: str = "") -> None:
    if msg:
        print(msg)
    if input("Proceed? [y/n] ") != "y":
        print("Exiting.")
        exit(1)


def normalize_greek_word(word: str) -> str:
    """
    Return a greek word without accents in lowercase.
    ["Άλφα", "Αλφα", "άλφα", "αλφα"] are all converted into "αλφα".

    >>> words = ["Άλφα", "Αλφα", "άλφα", "αλφα"]
    >>> normalized_words = [normalize_greek_word(w) for w in words]
    >>> assert len(set(normalized_words)) == 1
    """
    normalized = unicodedata.normalize("NFKD", word).casefold()
    return "".join(c for c in normalized if not unicodedata.combining(c))


def sort_greek_words(word: str) -> tuple[float, ...]:
    """
    Sort greek words while ignoring case and accents:

    >>> words = ['Βελάκι', 'άλφα', 'αλφάδι', 'Άρτεμις', 'Άλφα', 'αλεπού']
    >>> words.sort(key=sort_greek_words)
    >>> ['αλεπού', 'άλφα', 'Άλφα', 'αλφάδι', 'Άρτεμις', 'Βελάκι']
    """
    if not word:
        return (float("inf"),)

    # fmt: off
    ALPHABET: dict[str, int] = {
        'α': 1, 'β': 2, 'γ': 3, 'δ': 4, 'ε': 5, 'ζ': 6, 'η': 7, 'θ': 8, 'ι': 9, 'κ': 10,
        'λ': 11, 'μ': 12, 'ν': 13, 'ξ': 14, 'ο': 15, 'π': 16, 'ρ': 17, 'σ': 18, 'τ': 19, 'υ': 20,
        'φ': 21, 'χ': 22, 'ψ': 23, 'ω': 24
    }
    # fmt: on

    return tuple(ALPHABET.get(normalize_greek_word(char), float("inf")) for char in word)


def get_greek_sorting_fn():
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Ι'. Η μάχη -> 10
    NUMERALS = "Α Β Γ Δ Ε ΣΤ Ζ Η Θ Ι ΙΑ ΙΒ ΙΓ ΙΔ ΙΕ ΙΣΤ ΙΖ".split()
    ORDER = [f"{num}'" for num in NUMERALS]

    def sorting_fn(x: str) -> int:
        return ORDER.index(x.split(".")[0])

    return sorting_fn


def get_roman_sorting_fn():
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Chapitre X.mp3 -> X
    # NOTE: requires pip install roman
    import roman

    def sorting_fn(x: str) -> int:
        return roman.fromRoman((x.split()[1]).split(".")[0])

    return sorting_fn


def read_sorted_folders(folder: str, mode: str) -> list[str]:
    """Supports human (natsort), roman (I < V) and greek (Β < Γ) sorting"""
    if mode == "human":
        sorting_fn = os_sorted
    elif mode == "greek":
        sorting_fn = get_greek_sorting_fn()
    elif mode == "roman":
        sorting_fn = get_roman_sorting_fn()
    else:
        raise NotImplementedError("Unsupported mode in read_folder")

    return [
        f
        for f in sorting_fn(os.listdir(folder))
        if os.path.isfile(os.path.join(folder, f)) and not f.startswith(".")
    ]


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"{colors.TIME}({f.__name__} {te-ts:2.2f}sec){colors.END}")
        return result

    return wrap


if __name__ == "__main__":
    pass
