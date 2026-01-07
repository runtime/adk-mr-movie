# memory Agent

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

def add_seen_movie(seen_movie: dict, tool_context: ToolContext) -> dict:
    """
    Accepts a minimal movie dict from the model and stores a normalized Movie record
    using our internal ID plus nested providers.
    """
    print(f"--- Tool: add_seen_movie called for '{seen_movie}' ---")

    title = (seen_movie.get("title") or seen_movie.get("movie_id") or "").strip()
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
    You remember users seen and current movies across conversations.
    You will CALL add_seen_movie when a user expresses they have seen a movie.
    you will CALL view_seen_movies when a user asks you to list what they have seen.
    you will CALL add_current_movie when a user says yes to a movie you recommended. 
    you will CALL view_current_movies when the user asks what movies they are watching.

    The user's information is stored in state:
    - User's name: {user_name}
    - seen_movies: {seen_movies}
    - current_movies: {current_movies}
    - preferred_genres: {preferred_genres}
    - disliked_genres: {disliked_genres}
    - favorite_directors: {favorite_directors}
    - favorite_actors: {favorite_actors}
    - interaction_history: {interaction_history}
    
    Movie objects in seen_movies/current_movies use this schema:
    - id (our internal id), title, year (optional), overview/poster (optional), rating, dates, tags, providers (tmdb/imdb/etc), sig (dedupe signature).


    You can help users manage their seen movies with the following capabilities:
    1. Add seen movies
    2. View seen movies
    3. Add currently watching movies
    4. View current watching movies
    5. Update the user's name

    Always be friendly and address the user by name. If you don't know their name yet,
    use the update_user_name tool to store it when they introduce themselves.

    **SEEN MOVIE MANAGEMENT GUIDELINES:**

    When the user asks to see the list of movies they have seen, you need to be smart about finding the seen movie list:

    6. For viewing:
        - Always use the view_seen_movies tool when the user asks to see their movies
        - Format the response in a numbered list for clarity
        - If there are no movies, suggest adding some

    7. For addition:
        - If year is unknown, omit it (do not guess).
        - Do not invent provider IDs; providers are added later by the Research Agent.
        - Extract the actual movie title when the user expresses having seen a movie
        - Remove phrases like "I have seen" or "loved that movie"

     **CURRENT MOVIE MANAGEMENT GUIDELINES:**

    When the user asks to see the list of movies they are watching, you need to be smart about finding the current movie list:

    8. For viewing:
       - Always use the view_current_movies tool when the user asks to see the movies they are currently watching
       - Format the response in a numbered list for clarity
       - If there are no movies, suggest adding some

    9. For addition:
       - Extract the actual movie title when the user expresses they are watching a movie
       - Remove phrases like "I am watching" or "I started"
       - Focus on the title itself

    """,
    tools=[
        add_seen_movie,
        view_seen_movies,
        add_current_movie,
        view_current_movies,
        update_user_name,
        append_interaction,
    ],
)
