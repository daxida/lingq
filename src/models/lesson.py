from dataclasses import dataclass


@dataclass
class Lesson:
    title: str
    collection_title: str
    url: str
    id_: str
    text: str
    audio: bytes | None
    timestamps: str | None
