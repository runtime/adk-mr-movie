# memory Agent
from datetime import datetime, timezone
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from typing import Any, Dict, List, Optional
import re
from movie_night_agent.models.movie import Movie, ProviderRecord, now_iso

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")

def _signature(title: str, year: Optional[int]) -> str:
    t = _slug(title)
    y = str(year) if year else ""
    return f"{t}:{y}"

def _find_existing_index(items: list[Dict[str, Any]], movie_id: str, sig: str) -> int:
    for i, m in enumerate(items):
        if movie_id and m.get("id") == movie_id:
            return i
        if sig and m.get("sig") == sig:
            return i
    return -1




# helpers _slug, _signature, _find_existing_index above

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def touch_movie_night(tool_context: ToolContext) -> dict:
    """Update movie_night.last_active_at each turn."""
    mn = tool_context.state.get("movie_night") or {}
    mn["last_active_at"] = now_iso()
    if "status" not in mn:
        mn["status"] = "in_progress"
    tool_context.state["movie_night"] = mn
    return {"action": "touch_movie_night", "movie_night": mn}

def complete_movie_night(chosen_movie_title: str, tool_context: ToolContext) -> dict:
    """Mark the current movie night as completed."""
    mn = tool_context.state.get("movie_night") or {}
    mn["status"] = "completed"
    mn["last_active_at"] = now_iso()
    mn["chosen_movie_title"] = chosen_movie_title
    mn["chosen_via_agent"] = None  # set true/false later if you want
    tool_context.state["movie_night"] = mn
    return {"action": "complete_movie_night", "movie_night": mn}

def add_seen_movie(seen_movie: dict, tool_context: ToolContext) -> dict:
    """
    Accepts a minimal movie dict from the model and stores a normalized Movie record
    using our internal ID plus nested providers.
    """
    print(f"--- Tool: add_seen_movie called for '{seen_movie}' ---")

    title = (seen_movie.get("title") or "").strip()
    providers = seen_movie.get("providers") or {}

    # If the save intent came through root, we expect hydration
    # If not hydrated, store it but mark as pending hydration
    if title and not providers.get("tmdb"):
        seen_movie.setdefault("tags", {})
        seen_movie["tags"]["needs_hydration"] = True

    year = seen_movie.get("year", None)
    overview = seen_movie.get("description", "") or ""
    poster = seen_movie.get("thumbnail", "") or ""
    watched = seen_movie.get("date_watched", "") or ""
    rating_val = seen_movie.get("rating", 0) or 0

    # Build our canonical Movie
    movie = Movie(
        title=title or "Untitled",
        year=year,
        overview=overview,
        poster=poster,
    )
    movie.tags.status = "seen"
    movie.tags.source = "user"
    movie.dates.watched = watched
    movie.rating.value = float(rating_val) if str(rating_val).strip() != "" else 0
    movie.rating.source = "user"

    # If a provider object was passed (future TMDB), keep it
    providers = seen_movie.get("providers")
    if isinstance(providers, dict):
        # best-effort: trust provider dict shape and store
        for name, rec in providers.items():
            if isinstance(rec, dict):
                movie.providers[name] = ProviderRecord(**rec)

    # Dedupe based on internal id OR signature
    sig = _signature(movie.title, movie.year)
    seen_movies = tool_context.state.get("seen_movies", [])
    idx = _find_existing_index(seen_movies, movie.id, sig)

    payload = movie.model_dump()
    payload["sig"] = sig

    if idx >= 0:
        # replace existing entry (refresh)
        seen_movies[idx] = payload
        action = "updated_seen_movie"
        msg = f'Updated seen movie: "{movie.title}"'
    else:
        seen_movies.append(payload)
        action = "added_seen_movie"
        msg = f'Added seen movie: "{movie.title}"'

    tool_context.state["seen_movies"] = seen_movies

    return {
        "action": action,
        "movie": payload,
        "message": msg,
        "count": len(seen_movies),
    }



# def add_seen_movie(seen_movie: dict, tool_context: ToolContext) -> dict:
#     """
#     Accepts a minimal movie dict from the model and stores a normalized Movie record
#     using our internal ID plus nested providers.
#     """
#     print(f"--- Tool: add_seen_movie called for '{seen_movie}' ---")
#
#     title = (seen_movie.get("title") or seen_movie.get("movie_id") or "").strip()
#     year = seen_movie.get("year", None)
#     overview = seen_movie.get("description", "") or ""
#     poster = seen_movie.get("thumbnail", "") or ""
#     watched = seen_movie.get("date_watched", "") or ""
#     rating_val = seen_movie.get("rating", 0) or 0
#
#     # Build our canonical Movie
#     movie = Movie(
#         title=title or "Untitled",
#         year=year,
#         overview=overview,
#         poster=poster,
#     )
#     movie.tags.status = "seen"
#     movie.tags.source = "user"
#     movie.dates.watched = watched
#     movie.rating.value = float(rating_val) if str(rating_val).strip() != "" else 0
#     movie.rating.source = "user"
#
#     # If a provider object was passed (future TMDB), keep it
#     providers = seen_movie.get("providers")
#     if isinstance(providers, dict):
#         # best-effort: trust provider dict shape and store
#         for name, rec in providers.items():
#             if isinstance(rec, dict):
#                 movie.providers[name] = ProviderRecord(**rec)
#
#     # Dedupe based on internal id OR signature
#     sig = _signature(movie.title, movie.year)
#     seen_movies = tool_context.state.get("seen_movies", [])
#     idx = _find_existing_index(seen_movies, movie.id, sig)
#
#     payload = movie.model_dump()
#     payload["sig"] = sig
#
#     if idx >= 0:
#         # replace existing entry (refresh)
#         seen_movies[idx] = payload
#         action = "updated_seen_movie"
#         msg = f'Updated seen movie: "{movie.title}"'
#     else:
#         seen_movies.append(payload)
#         action = "added_seen_movie"
#         msg = f'Added seen movie: "{movie.title}"'
#
#     tool_context.state["seen_movies"] = seen_movies
#
#     return {
#         "action": action,
#         "movie": payload,
#         "message": msg,
#         "count": len(seen_movies),
#     }
#



def _movie_display(m: Dict[str, Any]) -> str:
    title = (m.get("title") or "Untitled").strip()
    year = m.get("year")
    providers = m.get("providers") or {}
    provider_tags = []
    if isinstance(providers, dict):
        if "tmdb" in providers and isinstance(providers["tmdb"], dict) and providers["tmdb"].get("id"):
            provider_tags.append(f"tmdb:{providers['tmdb']['id']}")
        if "imdb" in providers and isinstance(providers["imdb"], dict) and providers["imdb"].get("id"):
            provider_tags.append(f"imdb:{providers['imdb']['id']}")
    suffix = ""
    if year:
        suffix += f" ({year})"
    if provider_tags:
        suffix += f" [{' | '.join(provider_tags)}]"
    return f"{title}{suffix}"

def view_seen_movies(tool_context: ToolContext) -> dict:
    """View all seen movies."""
    print("--- Tool: view_seen_movies called ---")

    seen_movies = tool_context.state.get("seen_movies", []) or []
    display = [_movie_display(m) for m in seen_movies if isinstance(m, dict)]

    return {
        "action": "view_seen_movies",
        "movies": seen_movies,          # full objects
        "display": display,             # friendly strings
        "count": len(seen_movies),
    }



def add_current_movie(current_movie: dict, tool_context: ToolContext) -> dict:
    print(f"--- Tool: add_current_movie called for '{current_movie}' ---")

    title = (current_movie.get("title") or current_movie.get("movie_id") or "").strip()
    year = current_movie.get("year", None)
    overview = current_movie.get("description", "") or ""
    poster = current_movie.get("thumbnail", "") or ""
    rating_val = current_movie.get("rating", 0) or 0

    movie = Movie(
        title=title or "Untitled",
        year=year,
        overview=overview,
        poster=poster,
    )
    movie.tags.status = "current"
    movie.tags.source = "user"
    movie.rating.value = float(rating_val) if str(rating_val).strip() != "" else 0
    movie.rating.source = "user"

    providers = current_movie.get("providers")
    if isinstance(providers, dict):
        for name, rec in providers.items():
            if isinstance(rec, dict):
                movie.providers[name] = ProviderRecord(**rec)

    sig = _signature(movie.title, movie.year)
    current_movies = tool_context.state.get("current_movies", [])
    idx = _find_existing_index(current_movies, movie.id, sig)

    payload = movie.model_dump()
    payload["sig"] = sig

    if idx >= 0:
        current_movies[idx] = payload
        action = "updated_current_movie"
        msg = f'Updated current movie: "{movie.title}"'
    else:
        current_movies.append(payload)
        action = "added_current_movie"
        msg = f'Added current movie: "{movie.title}"'

    tool_context.state["current_movies"] = current_movies

    return {
        "action": action,
        "movie": payload,
        "message": msg,
        "count": len(current_movies),
    }

def view_current_movies(tool_context: ToolContext) -> dict:
    """View all current movies."""
    print("--- Tool: view_current_movies called ---")

    current_movies = tool_context.state.get("current_movies", []) or []
    display = [_movie_display(m) for m in current_movies if isinstance(m, dict)]

    return {
        "action": "view_current_movies",
        "movies": current_movies,       # full objects (same key as seen)
        "display": display,             # friendly strings
        "count": len(current_movies),
    }


def update_user_name(name: str, tool_context: ToolContext) -> dict:
    """Update the user's name.

    Args:
        name: The new name for the user
        tool_context: Context for accessing and updating session state

    Returns:
        A confirmation message
    """
    print(f"--- Tool: update_user_name called with '{name}' ---")

    # Get current name from state
    old_name = tool_context.state.get("user_name", "")

    # Update the name in state
    tool_context.state["user_name"] = name

    return {
        "action": "update_user_name",
        "old_name": old_name,
        "new_name": name,
        "message": f"Updated your name to: {name}",
    }

def append_interaction(entry: dict, tool_context: ToolContext) -> dict:
    """Append an interaction entry to state['interaction_history']."""
    history = tool_context.state.get("interaction_history", [])
    history.append(entry)
    tool_context.state["interaction_history"] = history
    return {"action": "append_interaction", "entry": entry, "count": len(history)}

# Create a persistent agent as our memory agent
memory_agent = Agent(
    name="memory_agent",
    model="gemini-2.5-flash",
    description="An agent with a persistent memory",
    instruction="""
    You are a persistence-only agent responsible for updating and reading user memory.
    You do NOT reason about recommendations or conversation flow. You only save and retrieve data.
    
    ### Core Responsibilities
    - Persist user identity, movie lists, and movie-night session state
    - Read memory when asked
    - Never invent data or infer intent beyond explicit user statements
    
    ### Mandatory Tool Usage
    - CALL touch_movie_night at the start of any turn where the user interacts.
    - CALL complete_movie_night only when the user explicitly confirms what they are going to watch tonight
      (e.g. “we’re going to watch X”, “we decided on X”, “we picked X”).
    
    ### Movie Persistence
    - CALL add_seen_movie when the user explicitly says they have seen a movie.
    - CALL add_current_movie when the user explicitly says they are watching a movie
      OR accepts a recommendation to watch.
    - CALL view_seen_movies when the user asks what they have seen.
    - CALL view_current_movies when the user asks what they are currently watching.
    
    ### User Identity
    - If the user provides their name and state['user_name'] is empty,
      CALL update_user_name to save it.
    
    ### Data Rules (CRITICAL)
    - Never guess or fabricate movie details.
    - If year is unknown, omit it.
    - Do NOT invent provider IDs.
    - Providers (tmdb/imdb/etc) are added only after Research Agent hydration.
    - Only extract the movie title from user statements (remove phrases like
      “I’ve seen”, “I’m watching”, “we loved”, etc).
    
    ### Movie Object Schema
    Movies stored in seen_movies or current_movies use this schema:
    - id (internal id)
    - title
    - year (optional)
    - overview / poster (optional)
    - rating (optional)
    - dates (watched/added)
    - tags
    - providers (tmdb, imdb, etc — optional)
    - sig (dedupe signature)
    
    ### State Access
    User data is stored in state:
    - user_name
    - seen_movies
    - current_movies
    - preferred_genres
    - disliked_genres
    - favorite_directors
    - favorite_actors
    - interaction_history
    - movie_night
    
    ### Tone
    - Be neutral and factual.
    - Do not generate conversational replies.
    - Do not ask follow-up questions.
    """,
    tools=[
        touch_movie_night,
        complete_movie_night,
        add_seen_movie,
        view_seen_movies,
        add_current_movie,
        view_current_movies,
        update_user_name,
        append_interaction,
    ],
)
