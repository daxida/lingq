from typing import Any

from pydantic import BaseModel


class Transliteration(BaseModel):
    # This:
    # - Has no keys for german or english
    # - Has exactly one key for greek: "transliteration": {"latin": ["paraschete"]}
    # - Has exactly three keys for japanese: "hiragana", "furigana" and "romaji".
    readings: dict[str, list[Any]] = {}
