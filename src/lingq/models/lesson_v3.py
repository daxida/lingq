"""Lesson model for API v3.

https://www.lingq.com/api/v3/el/lessons/31145860/
"""

from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel

from lingq.log import logger
from lingq.models.collection_v3 import CollectionV3
from lingq.models.hint import Hint
from lingq.models.readings import Readings
from lingq.models.transliteration import Transliteration

LockedReason = Literal[
    "NORMALIZE_AUDIO",
    "GENERATE_LIPP",
    "GENERATE_TIMESTAMPS",
    "TRANSCRIBE_AUDIO",
    "TOKENIZE_TEXT",
]

LOCKED_REASON_CHOICES: list[LockedReason] = list(get_args(LockedReason))


class Token(BaseModel):
    opentag: str | None = None
    text: str | None = None
    word_id: int | None = None
    index_in_sentence: int | None = None
    transliteration: Transliteration = Transliteration()
    index: int | None = None
    closetag: str | None = None


class TokenGroup(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    tokens: list[Token]
    text: str
    normalized_text: str
    # There is even [0, null]...
    timestamp: tuple[float | None, float | None]
    index: int


class LessonTranslation(BaseModel):
    method: str | None
    language: str
    sentences: list[str | None]


class Word(BaseModel):
    status: str
    tags: list[str] = []
    importance: int
    text: str
    readings: Readings = Readings()
    hints: list[Hint] | None = []


class Metadata(BaseModel):
    import_method: str | None = None
    splitting_method: str | None = None


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
    original_url: HttpUrl | Literal[""] | None
    image_url: HttpUrl
    original_image_url: HttpUrl
    provider_image_url: HttpUrl | None
    title: str
    description: str
    duration: int
    audio_url: HttpUrl | None
    audio_pending: bool
    give_rose_url: str
    word_count: int
    unique_word_count: int
    pub_date: str
    shared_date: str | None
    shared_by_id: int
    shared_by_name: str
    shared_by_role: str | None
    external_type: str | None
    type: str
    # P := shared, D := private, R := rejected, X := None
    status: Literal["P", "D", "R", "X"]
    pos: int
    price: int
    opened: bool
    completed: bool
    percent_completed: float
    new_words_count: int
    difficulty: float
    provider_name: str | None
    provider_description: str | None
    last_rose_received: str | None
    lesson_rating: int
    lesson_votes: int
    audio_rating: int
    audio_votes: int
    roses_count: int
    is_favorite: bool
    is_over_limit: bool | None
    level: str | None
    tags: list[str]
    # Sometimes it is just an empty string...
    provider_url: str | None
    read_times: float
    listen_times: float
    rose_given: bool
    open_date: str | None
    views_count: int
    is_protected: int | None
    scheduled_for_deletion: bool
    metadata: Metadata | None
    classic_url: str | None
    collection: CollectionV3
    folders: list[int]
    is_legacy: bool
    simplified_to: str | None
    simplified_by: str | None
    tokenized_text: list[list[TokenGroup]]
    is_locked: bool | LockedReason | None
    shared_by_image_url: HttpUrl
    shared_by_is_friend: bool
    print_url: str | None
    can_edit: bool
    can_edit_sentence: bool
    bookmark: dict[str, Any]
    next_lesson_id: int | None = None
    previous_lesson_id: int | None = None
    previous_lesson: PreviousLesson | None = None
    next_lesson: PreviousLesson | None = None
    translation: LessonTranslation | None
    video_url: str | None
    cards: dict[str, Any]
    cards_count: int
    words: dict[str, Word]

    # Custom attributes
    _downloaded_audio: bytes | None = None
    _timestamps: str | None = None

    def get_raw_text(self) -> str:
        # The first element is the lesson title, that we don't use.
        # Note that some defective lessons may not have a title,
        # and makes us skip the first paragraph.
        return "\n".join(" ".join(t.text for t in tokens) for tokens in self.tokenized_text[1:])

    def to_vtt(self) -> str | None:
        vtt_lines = ["WEBVTT\n"]

        idx_token = 0
        # The first element is the lesson title, that we don't use.
        # Note that some defective lessons may not have a title,
        # and makes us skip the first paragraph.
        for paragraph_data in self.tokenized_text[1:]:
            for token_group in paragraph_data:
                start_time, end_time = token_group.timestamp
                if start_time is None or end_time is None:
                    # Early exit: the text has no timestamps
                    logger.warning(f"Lesson {self.title} has no subtitles")
                    return None
                start = format_timestamp(start_time)
                end = format_timestamp(end_time)

                idx_token += 1
                vtt_lines.append(f"{idx_token}")
                vtt_lines.append(f"{start} --> {end}")
                vtt_lines.append(token_group.text)
                vtt_lines.append("")

        return "\n".join(vtt_lines)


def format_timestamp(seconds: float) -> str:
    """Format seconds to VTT format (HH:MM:SS.mmm)."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds * 1000) % 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"
