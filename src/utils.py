import os
import time
from functools import wraps
from typing import List

from natsort import os_sorted

# fmt: off
RED    = "\033[31m"  # Error
GREEN  = "\033[32m"  # Success
YELLOW = "\033[33m"  # Skips
CYAN   = "\033[36m"  # Timings
RESET  = "\033[0m"
# fmt: on


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


def read_sorted_folders(folder: str, mode: str) -> List[str]:
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
        print(f"{CYAN}({f.__name__} {te-ts:2.2f}sec){RESET}")
        return result

    return wrap
