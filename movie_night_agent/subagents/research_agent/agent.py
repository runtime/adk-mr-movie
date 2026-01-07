from __future__ import annotations

from typing import Any, Dict, Optional

from google.adk.agents import Agent

from .tmdb import search_movie, movie_details
from movie_night_agent.models.movie import now_iso


def _poster_url(path: Optional[str]) -> str:
    return f"https://image.tmdb.org/t/p/w500{path}" if path else ""


def _year(release_date: Optional[str]) -> Optional[int]:
    if not release_date or len(release_date) < 4:
        return None
    try:
        return int(release_date[:4])
    except Exception:
        return None


async def find_title(title: str, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Find a movie by title (optionally year) on TMDB.
    Returns {found:false} if none.
    """
    hit = await search_movie(title=title, year=year)
    if not hit:
        return {"found": False, "title": title, "year": year}

    return {
        "found": True,
        "tmdb_id": hit.get("id"),
        "title": hit.get("title") or title,
        "year": _year(hit.get("release_date")),
        "description": hit.get("overview") or "",
        "thumbnail": _poster_url(hit.get("poster_path")),
        "rating": hit.get("vote_average") or 0,
    }


async def get_movie_details(tmdb_id: int) -> Dict[str, Any]:
    """
    Hydrate a movie from TMDB and return a dict that your Memory Agent can save
    into your canonical Movie schema: core fields + providers.tmdb.
    """
    raw = await movie_details(tmdb_id)

    title = raw.get("title") or ""
    year = _year(raw.get("release_date"))
    overview = raw.get("overview") or ""
    poster = _poster_url(raw.get("poster_path"))
    rating = raw.get("vote_average") or 0

    hydrated = {
        "title": title,
        "year": year,
        "rating": rating,
        "poster_url": poster,
        "overview": overview,
        "runtime": raw.get("runtime"),
        "genres": [g.get("name") for g in (raw.get("genres") or []) if isinstance(g, dict)],
    }

    return {
        # Fields your memory agent already maps into Movie(...)
        "title": title,
        "year": year,
        "description": overview,
        "thumbnail": poster,
        "rating": rating,

        # Provider payload (your “our id + providers” design)
        "providers": {
            "tmdb": {
                "id": tmdb_id,
                "hydrated": hydrated,
                "raw": raw,  # optional; keep for now
                "last_fetched": now_iso(),
            }
        },
    }


research_agent = Agent(
    name="research_agent",
    model="gemini-2.5-flash",
    description="Hydrates movie facts from TMDB and returns providers.tmdb payload.",
    instruction="""
You use TMDB to look up and hydrate movie information.

When the user asks for more information about a movie, or when we need details before saving:
1) Call find_title(title, year?) to get a tmdb_id.
2) Call get_movie_details(tmdb_id) to return a dict containing:
   - title/year/description/thumbnail/rating
   - providers.tmdb with {id, hydrated, raw, last_fetched}

If find_title returns found:false, ask the user to clarify the title or provide a year.
Do not invent TMDB ids.
""",
    tools=[
        find_title,
        get_movie_details
    ],
)
