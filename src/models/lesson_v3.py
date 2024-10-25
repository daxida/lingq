from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel

from models.collection_v3 import CollectionV3
from models.hint import Hint
from models.readings import Readings
from models.transliteration import Transliteration


class Token(BaseModel):
    opentag: Optional[str] = None
    text: Optional[str] = None
    word_id: Optional[int] = None
    index_in_sentence: Optional[int] = None
    transliteration: Transliteration = Transliteration()
    index: Optional[int] = None
    closetag: Optional[str] = None


class TokenGroup(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    tokens: list[Token]
    text: str
    normalized_text: str
    timestamp: list[Optional[Any]]
    index: int


class LessonTranslation(BaseModel):
    method: str
    language: str
    sentences: list[Optional[str]]


class Word(BaseModel):
    status: str
    tags: list[str]
    importance: int
    text: str
    readings: Readings = Readings()
    hints: Optional[list[Hint]] = []


class Metadata(BaseModel):
    splitting_method: str
    import_method: str


class PreviousLesson(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    price: int
    collection_title: str
    is_taken: bool
    shared_by_id: int
    status: str
    title: str
    image: HttpUrl
    id: int


class LessonV3(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    content_id: int
    collection_id: int
    collection_title: str
    url: HttpUrl
    original_url: Optional[HttpUrl] | Literal[""]
    image_url: HttpUrl
    original_image_url: HttpUrl
    provider_image_url: Optional[HttpUrl]
    title: str
    description: str
    duration: int
    audio_url: Optional[HttpUrl]
    audio_pending: bool
    give_rose_url: str
    word_count: int
    unique_word_count: int
    pub_date: str
    shared_date: Optional[str]
    shared_by_id: int
    shared_by_name: str
    shared_by_role: Optional[str]
    external_type: Optional[str]
    type: str
    status: str
    pos: int
    price: int
    opened: bool
    completed: bool
    percent_completed: int
    new_words_count: int
    difficulty: float
    provider_name: Optional[str]
    provider_description: Optional[str]
    last_rose_received: Optional[str]
    lesson_rating: int
    lesson_votes: int
    audio_rating: int
    audio_votes: int
    roses_count: int
    is_favorite: bool
    is_over_limit: Optional[bool]
    level: Optional[str]
    tags: list[str]
    # Sometimes it is just an empty string...
    provider_url: Optional[HttpUrl] | Literal[""]
    read_times: float
    listen_times: int
    rose_given: bool
    open_date: Optional[str]
    views_count: int
    is_protected: Optional[int]
    scheduled_for_deletion: bool
    metadata: Optional[Metadata]
    classic_url: Optional[str]
    collection: CollectionV3
    folders: list[int]
    is_legacy: bool
    simplified_to: Optional[str]
    simplified_by: Optional[str]
    tokenized_text: list[list[TokenGroup]]
    is_locked: Optional[bool]
    shared_by_image_url: HttpUrl
    shared_by_is_friend: bool
    print_url: Optional[str]
    can_edit: bool
    can_edit_sentence: bool
    bookmark: dict[str, Any]
    next_lesson_id: Optional[int]
    previous_lesson_id: Optional[int]
    previous_lesson: Optional[PreviousLesson]
    next_lesson: Optional[Any]
    translation: Optional[LessonTranslation]
    video_url: Optional[str]
    cards: dict[str, Any]
    cards_count: int
    words: dict[str, Word]
