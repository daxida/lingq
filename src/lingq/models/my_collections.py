from pydantic import BaseModel, Field


class CollectionItem(BaseModel):
    id: int
    title: str
    image_url: str = Field(..., alias="imageUrl")


class MyCollections(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[CollectionItem]
