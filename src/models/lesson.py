from dataclasses import dataclass


@dataclass
class SimpleLesson:
    title: str
    collection_title: str
    url: str
    id_: int
    text: str
    audio: bytes | None
    timestamps: str | None
