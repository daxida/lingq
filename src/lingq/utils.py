import sys
import time
import unicodedata
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, Literal, Type

import roman
from natsort import natsort_keygen, os_sorted
from pydantic import BaseModel, ValidationError

from lingq.log import logger


def double_check(msg: str = "", assume_yes: bool = False) -> None:
    if assume_yes:
        return
    if msg:
        print(msg)
    if input("Proceed? [y/n] ") != "y":
        print("Exiting.")
        exit(1)


ContentType = Literal["lesson", "course"]


def get_editor_url(lang: str, content_id: int, content_type: ContentType) -> str:
    base = f"https://www.lingq.com/learn/{lang}/web/editor"
    if content_type == "course":
        base = f"{base}/courses"
    return f"{base}/{content_id}"


def model_validate_or_exit[T: BaseModel](
    pydantic_model: Type[T],
    obj: Any,
    lang: str,
    content_id: int,
    content_type: ContentType,
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


def sort_by_greek_words_impl(word: str) -> tuple[float, ...]:
    """Sort greek words while ignoring case and accents.

    >>> words = ["Βελάκι", "άλφα", "αλφάδι", "Άρτεμις", "Άλφα", "αλεπού"]
    >>> words.sort(key=sort_greek_words)
    >>> ["αλεπού", "άλφα", "Άλφα", "αλφάδι", "Άρτεμις", "Βελάκι"]
    """
    if not word:
        return (float("inf"),)
    return tuple(ord(normalize_greek_word(char)) for char in word)


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


SortingMode = Literal["os", "human", "greek", "roman"]
"""List of sorted modes. Used for reading folder contents."""


def get_sorting_fn(mode: SortingMode) -> Callable[[str], Any]:
    """Get the sorting function from a mode.

    Supports human (natsort), roman (I < V) and greek (Β < Γ) sorting.
    """
    sorting_fn: Callable[[str], Any]
    match mode:
        case "os":
            # Sort elements in the same order as your operating system's file browser
            # Note that this is platform-dependent
            sorting_fn = os_sorted
        case "human":
            sorting_fn = natsort_keygen()
        case "greek":
            sorting_fn = greek_sorting_fn
        case "roman":
            sorting_fn = roman_sorting_fn
    return sorting_fn


def sorted_subpaths(folder: Path, mode: SortingMode) -> list[Path]:
    """Returns subfolders sorted by sorting_fn."""
    sorting_fn = get_sorting_fn(mode)
    subfolders = [sf for sf in folder.iterdir() if not sf.name.startswith(".")]
    subfolders.sort(key=lambda x: sorting_fn(x.name))
    return subfolders


# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
def timing[**P, T](f: Callable[P, T]) -> Callable[P, T]:
    @wraps(f)
    def wrap(*args: P.args, **kw: P.kwargs) -> T:
        ts = time.time()
        result = f(*args, **kw)
        te = time.time()
        print(f"\033[36m({f.__name__} {te - ts:2.2f}sec)\033[0m")  # type: ignore[attr-defined]
        return result

    return wrap


if __name__ == "__main__":
    pass
