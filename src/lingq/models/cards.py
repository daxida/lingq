from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from lingq.models.hint import Hint
from lingq.models.readings import Readings
from lingq.models.transliteration import Transliteration


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
    # LingQ importance (their own undocumented custom ranking)
    importance: int
    # LingQ status (0-3)
    # 0 : new (displays as 1 in the website)
    # 1 : recognized
    # 2 : familiar
    # 3 : learned
    # 3 : known (+ requires extended_status to be 3)
    status: int
    extended_status: int | None = None
    # last_reviewed_correct: str | None = None
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

    def displayed_status(self) -> int:
        assert 0 <= self.status <= 3
        if self.status < 3:
            return self.status + 1
        return 5 if self.extended_status == 3 else 4


class Cards(BaseModel):
    count: int
    next: str | None = None
    previous: str | None = None
    results: list[Card]
