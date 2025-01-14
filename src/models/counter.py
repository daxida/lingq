from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Counter(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    cards_count: int
    has_flags: bool
    known_words_count: int
    total_words_count: int
    rose_given: bool
    roses_count: int
    lessons_count: int
    difficulty: float
    is_taken: bool
    new_words_count: int
    pk: int
    progress: float | None = None
    listen_times: float | None = None
    is_completely_taken: bool
    unique_words_count: int
    read_times: float | None = None
