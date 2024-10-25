from typing import Optional

from pydantic import BaseModel


class Hint(BaseModel):
    id: int
    locale: str
    text: str
    term: Optional[str] = None
    popularity: int
    is_google_translate: bool
    flagged: bool
