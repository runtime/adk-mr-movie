from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl
import ulid


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_movie_id() -> str:
    return f"mv_{ulid.new()}"


class Rating(BaseModel):
    value: float = 0
    scale: int = 10
    source: Literal["user", "tmdb", "imdb", "unknown"] = "unknown"


class Dates(BaseModel):
    added: str = Field(default_factory=now_iso)
    watched: str = ""  # optional


class Tags(BaseModel):
    status: Literal["seen", "current"] = "seen"
    source: Literal["user", "tmdb", "imdb", "unknown"] = "unknown"
    genres: list[str] = Field(default_factory=list)


class ProviderRecord(BaseModel):
    id: Optional[Any] = None  # TMDB int, IMDB string, etc.
    hydrated: Dict[str, Any] = Field(default_factory=dict)
    raw: Dict[str, Any] = Field(default_factory=dict)
    last_fetched: str = ""


class Movie(BaseModel):
    id: str = Field(default_factory=new_movie_id)

    title: str
    year: Optional[int] = None
    overview: str = ""
    poster: str = ""

    rating: Rating = Field(default_factory=Rating)
    dates: Dates = Field(default_factory=Dates)
    tags: Tags = Field(default_factory=Tags)

    providers: Dict[str, ProviderRecord] = Field(default_factory=dict)

    def provider_id(self, name: str) -> Optional[Any]:
        rec = self.providers.get(name)
        return rec.id if rec else None
