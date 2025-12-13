from pydantic import BaseModel


class Readings(BaseModel):
    readings: dict[str, list[str]] = {}
