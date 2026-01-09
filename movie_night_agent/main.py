import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from .agent import agent # <-- mr movie agent
from .utils.call_agent_async import call_agent_async # <-- async agent util for cli
import inspect


load_dotenv()

# 1. initialize storage
db_url = "sqlite:///./mr_movie.db"
# create the session service as a db service
session_service = DatabaseSessionService(db_url=db_url)

# check what methods it has to debug versioning
print("SessionService methods (session/state):",
      [m for m in dir(session_service) if "session" in m.lower() or "state" in m.lower()])

print("update sig:", inspect.signature(session_service._update_session_state))

# 2. define initial state
# get the user & user prefs as initial state


def now_iso():
    return datetime.now(timezone.utc).isoformat()

initial_state = {
    "user_name": None,

    # --- profile-ish memory (for now; later this becomes profile scoped) ---
    "seen_movies": [],
    "current_movies": [],
    "preferred_genres": [],
    "disliked_genres": [],
    "favorite_directors": [],
    "favorite_actors": [],
    "interaction_history": [],

    # --- movie-night session memory (tab-like) ---
    "movie_night": {
        "status": "in_progress",          # in_progress | completed
        "created_at": now_iso(),
        "last_active_at": now_iso(),
        "participants": [],               # future: ["profile:erik", "profile:gf"]
        "subject_movie_id": None,         # the “current” movie being discussed (optional)
        "chosen_movie_id": None,          # set when completed
        "chosen_movie_title": None,       # convenience
        "chosen_via_agent": None,         # true/false
        "constraints": {                  # future-friendly
            "mood": None,
            "genres": [],
            "max_runtime_min": None,
            "providers": []
        }
    },
}



# create async main function
async def main_async():
    # local constants
    APP_NAME = "mr_movie"
    USER_ID = "mrmovieagent"  # <-- user.id (eventually comes from token)

    for app in ["agent", "mr_movie"]:
        s = await session_service.list_sessions(app_name=app, user_id=USER_ID)
        print(app, [x.id for x in (s.sessions or [])])

    # 3. session management, find or crate
    # a. look for sessions
    existing_sessions = await session_service.list_sessions(
        app_name=APP_NAME,
        user_id=USER_ID,
    )
    # b. if there is a session, use it otherwise create new
    # if existing_sessions and len(existing_sessions.sessions) > 0:
    if existing_sessions and len(existing_sessions.sessions) > 0:
        print(f'existing sessions: {existing_sessions.sessions[0].id}')
        #SESSION_ID = existing_sessions.sessions[0].id
        SESSION_ID = existing_sessions.sessions[0].id
        print(f"continuing session: {SESSION_ID}")
    else:
        # c. create new session with initial state as one does not exit
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state=initial_state
        )
        SESSION_ID = session.id
        print(f"created new session {SESSION_ID}")

    # 4. agent runner setup
    #create a runner with the root agent, mr movie
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print(f'runner: {runner}')
    # 5. interactive conversation loop
    print("\n 🍿 Welcome to Mr. Movie!")
    print("\n 👉🏼 I'm Your Movie BFF who helps you pick a movie based on your preferences and stuff")
    print("\n 🔧 Type 'exit' or 'quit' to end the conversation\n")

    while True:
        # Get user input
        user_input = input("You: ")

        # check for exit
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation, Your data has been saved to the Mr. Movie database")
            break

        # todo update interaction history with users query
        # add_user_query_to_history( session_service, APP_NAME, USER_ID, SESSION_ID, user_input )

        # call process user query through the agent
        result = await call_agent_async(runner, USER_ID, SESSION_ID, user_input)
        print(f'main: call_agent_async result.tool_calls: {result.tool_calls}')
        print(f'main: call_agent_async result.tool_outputs: {result.tool_outputs}')


if __name__ == "__main__":
    asyncio.run(main_async())