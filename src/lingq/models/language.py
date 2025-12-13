"""Lesson model for API v2.

https://www.lingq.com/apidocs/api-2.0.html#get (outdated)

https://www.lingq.com/api/v2/languages/
"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Language(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    url: str
    code: str  # eo
    title: str  # Esperanto
    supported: bool
    known_words: int
    # last_used: str | None
    # grammar_resource_slug: str
    # schedule_for_deletion: bool
