from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel


class CollectionSource(BaseModel):
    type: str | None
    name: str
    url: str | None


class CollectionV3(BaseModel):
    """Collection model for API v3.

    https://www.lingq.com/api/v3/el/collections/1765504/
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    type: str
    title: str
    status: str
    source: CollectionSource | None
    is_taken: bool | None
    image_url: HttpUrl
    audio_pending: bool
    original_image_url: HttpUrl | None
    provider_image_url: HttpUrl | None
    shared_by_image_url: HttpUrl
    provider_id: int | None
    provider_name: str | None
    shared_by_id: int
    shared_by_name: str
    shared_by_role: str | None
    description: str
    is_featured: bool | None
    is_locked: bool | None
    lessons_count: int
    new_words_count: int
    difficulty: float
    roses_count: int
    views_count: int
    duration: int
    progress: str | None
    # metadata: dict | None
    folders: list[int]
    accent: str | None
    level: str | None
    price: int
    date: str
    tags: list[str]
    url: str


"""https://www.lingq.com/api/v3/el/collections/1765504/lessons/"""


class CollectionLessonResult(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    url: str
    type: str
    date: str
    level: str | None
    title: str
    description: str | None
    accent: str | None
    collection_id: int
    collection_title: str
    audio: str | None
    image_url: str | None
    original_image_url: str | None
    provider_id: int | None
    provider_image_url: str | None
    provider_name: str | None
    shared_by_id: int
    shared_by_name: str
    status: Literal["private", "shared", "rejected", "inaccessible", "pending"] | None
    percent_completed: float
    is_over_limit: bool | None
    is_protected: bool | None
    is_featured: bool | None
    views_count: int
    word_count: int
    unique_word_count: int
    new_words_count: int
    listen_times: float
    difficulty: float
    source_type: str | None
    source_url: str | None
    source: CollectionSource | None
    duration: int
    price: int
    tags: list[str]
    folders: list[int]
    shelves: list[str]
    video_url: str | None
    can_edit: bool


class CollectionLessons(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[CollectionLessonResult]


"""https://www.lingq.com/api/v3/el/search/?shelf=my_lessons&type=collection"""


class SearchCollectionResult(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    type: str
    title: str
    status: str
    source: CollectionSource | None
    is_taken: bool | None
    image_url: str | None
    audio_pending: bool
    original_image_url: str | None
    provider_image_url: str | None
    shared_by_image_url: str | None
    provider_id: int | None
    provider_name: str | None
    shared_by_id: int
    shared_by_name: str
    shared_by_role: str | None
    description: str | None
    is_featured: bool | None
    is_locked: bool | None
    lessons_count: int
    new_words_count: int
    difficulty: float
    roses_count: int
    views_count: int
    duration: int
    progress: float | None
    # metadata
    folders: list[int]
    accent: str | None
    level: str | None
    price: int
    date: str
    tags: list[str]
    url: str


class SearchCollections(BaseModel):
    next: str | None
    previous: str | None
    results: list[SearchCollectionResult]
