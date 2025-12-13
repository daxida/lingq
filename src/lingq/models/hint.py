from pydantic import BaseModel


class Hint(BaseModel):
    id: int
    locale: str
    text: str
    term: str | None = None
    popularity: int
    is_google_translate: bool
    flagged: bool
