from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from models.hint import Hint
from models.readings import Readings
from models.transliteration import Transliteration


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
    audio: str | None = None
    words: list[str]
    tags: list[str]
    hints: list[Hint]
    transliteration: Transliteration = Transliteration()
    g_tags: list[str]
    word_tags: list[str]
    readings: Readings = Readings()
    writings: list[str]


class Cards(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[Card]
