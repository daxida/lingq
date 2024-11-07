from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel


class CollectionSource(BaseModel):
    type: str | None
    name: str
    url: str | None


class CollectionV3(BaseModel):
    """https://www.lingq.com/api/v3/el/collections/1765504/"""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    type: str
    title: str
    status: str
    source: Optional[CollectionSource]
    is_taken: Optional[bool]
    image_url: HttpUrl
    audio_pending: bool
    original_image_url: Optional[HttpUrl]
    provider_image_url: Optional[HttpUrl]
    shared_by_image_url: HttpUrl
    provider_id: Optional[int]
    provider_name: Optional[str]
    shared_by_id: int
    shared_by_name: str
    shared_by_role: Optional[str]
    description: str
    is_featured: Optional[bool]
    is_locked: Optional[bool]
    lessons_count: int
    new_words_count: int
    difficulty: float
    roses_count: int
    views_count: int
    duration: int
    progress: Optional[str]
    metadata: Optional[dict]
    folders: list[int]
    accent: Optional[str]
    level: Optional[str]
    price: int
    date: str
    tags: list[str]
    url: str


"""https://www.lingq.com/api/v3/el/collections/1765504/lessons/"""

from pydantic import FailFast
from typing_extensions import Annotated


class CollectionLessonResult(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    url: str
    type: str
    date: str
    level: Optional[str]
    title: str
    description: Optional[str]
    accent: Optional[str]
    collection_id: int
    collection_title: str
    audio: Optional[str]
    image_url: Optional[str]
    original_image_url: Optional[str]
    provider_id: Optional[int]
    provider_image_url: Optional[str]
    provider_name: Optional[str]
    shared_by_id: int
    shared_by_name: str
    status: Literal["private", "shared", "rejected", "inaccessible"] | None
    percent_completed: float
    is_over_limit: Optional[bool]
    is_protected: Optional[bool]
    is_featured: Optional[bool]
    views_count: int
    word_count: int
    unique_word_count: int
    new_words_count: int
    listen_times: float
    difficulty: float
    source_type: Optional[str]
    source_url: Optional[str]
    source: Optional[CollectionSource]
    duration: int
    price: int
    tags: list[str]
    folders: list[int]
    shelves: list[str]
    video_url: Optional[str]
    can_edit: bool


class CollectionLessons(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: Annotated[list[CollectionLessonResult], FailFast()]


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
    source: Optional[CollectionSource]
    is_taken: Optional[bool]
    image_url: Optional[str]
    audio_pending: bool
    original_image_url: Optional[str]
    provider_image_url: Optional[str]
    shared_by_image_url: Optional[str]
    provider_id: Optional[int]
    provider_name: Optional[str]
    shared_by_id: int
    shared_by_name: str
    shared_by_role: Optional[str]
    description: Optional[str]
    is_featured: Optional[bool]
    is_locked: Optional[bool]
    lessons_count: int
    new_words_count: int
    difficulty: float
    roses_count: int
    views_count: int
    duration: int
    progress: Optional[float]
    # metadata
    folders: list[int]
    accent: Optional[str]
    level: Optional[str]
    price: int
    date: str
    tags: list[str]
    url: str


class SearchCollections(BaseModel):
    next: str | None
    previous: str | None
    results: Annotated[list[SearchCollectionResult], FailFast()]
