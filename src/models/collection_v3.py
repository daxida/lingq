from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, HttpUrl
from pydantic.alias_generators import to_camel


class CollectionSource(BaseModel):
    type: Literal["indirect", "direct"]
    name: str
    url: HttpUrl


class CollectionV3(BaseModel):
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
