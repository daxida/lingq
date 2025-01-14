import sys
import time
import unicodedata
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, Literal, Type, TypeVar

import roman  # type: ignore
from natsort import natsort_keygen, os_sorted
from pydantic import BaseModel, ValidationError

from log import logger


def double_check(msg: str = "") -> None:
    if msg:
        print(msg)
    if input("Proceed? [y/n] ") != "y":
        print("Exiting.")
        exit(1)


def get_editor_url(lang: str, content_id: int, content_type: Literal["lesson", "course"]) -> str:
    base = f"https://www.lingq.com/learn/{lang}/web/editor"
    if content_type == "course":
        base = f"{base}/courses"
    return f"{base}/{content_id}"


def model_validate_or_exit[T: BaseModel](
    pydantic_model: Type[T],
    obj: Any,
    lang: str,
    content_id: int,
    content_type: Literal["lesson", "course"],
) -> T:
    """Try to validate the pydantic model.

    In case of failure, log the error and exit the program. This makes
    debugging less cumbersome than to decypher the long async stacktrace.
    """
    try:
        return pydantic_model.model_validate(obj)
    except ValidationError as e:
        message = (
            f"Error validating model for {content_type} with id {content_id}\n"
            f"Editor URL: {get_editor_url(lang, content_id, content_type)}\n"
            f"Details: {e}"
        )
        logger.error(message)
        sys.exit(1)


def normalize_greek_word(word: str) -> str:
    """Return a greek word without accents in lowercase.
    ["Άλφα", "Αλφα", "άλφα", "αλφα"] are all converted into "αλφα".

    >>> words = ["Άλφα", "Αλφα", "άλφα", "αλφα"]
    >>> normalized_words = [normalize_greek_word(w) for w in words]
    >>> assert len(set(normalized_words)) == 1
    """
    normalized = unicodedata.normalize("NFKD", word).casefold()
    return "".join(c for c in normalized if not unicodedata.combining(c))


def sort_greek_words(word: str) -> tuple[float, ...]:
    """Sort greek words while ignoring case and accents.

    >>> words = ["Βελάκι", "άλφα", "αλφάδι", "Άρτεμις", "Άλφα", "αλεπού"]
    >>> words.sort(key=sort_greek_words)
    >>> ["αλεπού", "άλφα", "Άλφα", "αλφάδι", "Άρτεμις", "Βελάκι"]
    """
    if not word:
        return (float("inf"),)

    # fmt: off
    alphabet: dict[str, int] = {
        "α": 1, "β": 2, "γ": 3, "δ": 4, "ε": 5, "ζ": 6, "η": 7, "θ": 8, "ι": 9, "κ": 10,
        "λ": 11, "μ": 12, "ν": 13, "ξ": 14, "ο": 15, "π": 16, "ρ": 17, "σ": 18, "τ": 19, "υ": 20,
        "φ": 21, "χ": 22, "ψ": 23, "ω": 24
    }
    # fmt: on

    return tuple(alphabet.get(normalize_greek_word(char), float("inf")) for char in word)


def greek_sorting_fn(x: str) -> int:
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Ι'. Η μάχη -> 10
    numerals = "Α Β Γ Δ Ε ΣΤ Ζ Η Θ Ι ΙΑ ΙΒ ΙΓ ΙΔ ΙΕ ΙΣΤ ΙΖ ΙΗ ΙΘ Κ ΚΑ ΚΒ ΚΓ ΚΔ ΚΕ ΚΣΤ ΚΖ ΚΗ ΚΘ"
    order = [f"{num}'" for num in numerals.split()]
    return order.index(x.split(".")[0])


def roman_sorting_fn(x: str) -> int:
    # This requires fine tuning depending of the entries' name format:
    # I was working with:
    # Chapitre X.mp3 -> X
    return roman.fromRoman((x.split()[1]).split(".")[0])  # type: ignore


def get_sorting_fn(mode: str) -> Callable[[str], Any]:
    """Get the sorting function from a mode.

    Supports human (natsort), roman (I < V) and greek (Β < Γ) sorting.
    """
    sorting_fn: Callable[[str], Any]
    if mode == "os":
        # Sort elements in the same order as your operating system's file browser
        # Note that this is platform-dependent
        sorting_fn = os_sorted
    elif mode == "human":
        sorting_fn = natsort_keygen()
    elif mode == "greek":
        sorting_fn = greek_sorting_fn
    elif mode == "roman":
        sorting_fn = roman_sorting_fn
    else:
        raise NotImplementedError("Unsupported mode in read_folder")
    return sorting_fn


def sorted_subpaths(folder: Path, mode: str) -> list[Path]:
    """Returns subfolders sorted by sorting_fn."""
    sorting_fn = get_sorting_fn(mode)
    subfolders = [sf for sf in folder.iterdir() if not sf.name.startswith(".")]
    subfolders.sort(key=lambda x: sorting_fn(x.name))
    return subfolders


R = TypeVar("R")


def timing(f: Callable[..., R]) -> Callable[..., R]:
    @wraps(f)
    def wrap(*args: Any, **kw: Any) -> R:
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"\033[36m({f.__name__} {te - ts:2.2f}sec)\033[0m")
        return result

    return wrap


if __name__ == "__main__":
    pass
