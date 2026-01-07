from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def _headers() -> Dict[str, str]:
    token = os.getenv("TMDB_READ_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("Missing TMDB_READ_ACCESS_TOKEN in environment.")
    return {"Authorization": f"Bearer {token}"}


async def search_movie(title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
    params: Dict[str, Any] = {"query": title, "include_adult": False}
    if year is not None:
        params["year"] = year

    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{TMDB_BASE_URL}/search/movie",
            params=params,
            headers=_headers(),
        )
        r.raise_for_status()
        payload = r.json()
        results = payload.get("results") or []
        return results[0] if results else None


async def movie_details(tmdb_id: int) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"{TMDB_BASE_URL}/movie/{tmdb_id}",
            headers=_headers(),
        )
        r.raise_for_status()
        return r.json()
