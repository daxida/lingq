from typing import Any, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Hint(BaseModel):
    id: int
    locale: str
    text: str
    term: str
    popularity: int
    is_google_translate: bool
    flagged: bool


class Transliteration(BaseModel):
    readings: dict[str, list[Any]] = {}


class Readings(BaseModel):
    readings: dict[str, list[str]] = {}


class Card(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    pk: int
    # Unused
    # url: str
    term: str
    fragment: str
    importance: int
    # LingQ status (0-4?)
    status: int
    # Unused
    # extended_status: Optional[int] = None
    # last_reviewed_correct: Optional[str] = None
    # srs_due_date: str
    notes: str
    audio: Optional[str] = None
    words: list[str]
    tags: list[str]
    hints: list[Hint]
    # This:
    # - Has no keys for german or english
    # - Has exactly one key for greek: "transliteration": {"latin": ["paraschete"]}
    # - Has exactly three keys for japanese: "hiragana", "furigana" and "romaji".
    transliteration: Transliteration = Transliteration()
    g_tags: list[str]
    word_tags: list[str]
    readings: Readings = Readings()
    writings: list[str]


class Cards(BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: list[Card]
