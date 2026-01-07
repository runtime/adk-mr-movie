# utils/call_agent_async.py
from __future__ import annotations
from google.genai import types
from .console import Colors, print_error, print_final_response, print_query_banner
from .events import RunResult, accumulate_result

async def display_state(session_service, app_name: str, user_id: str, session_id: str, label: str) -> None:
    """
    Kept here (not in console.py) so it’s clearly part of runtime orchestration.
    Later you can swap these prints for logs without touching console formatting helpers.
    """
    try:
        session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        print(f"\n{'-' * 10} {label} {'-' * 10}")
        print(f"👤 User: {session.state.get('user_name', 'Unknown')}")
        print(f"📝 seen_movies: {len(session.state.get('seen_movies', []) or [])}")
        print(f"🎬 current_movies: {len(session.state.get('current_movies', []) or [])}")
        print(f"🧠 interaction_history: {len(session.state.get('interaction_history', []) or [])}")
        print("-" * (22 + len(label)))
    except Exception as e:
        print_error(f"Error displaying state: {e}")

async def call_agent_async(runner, user_id: str, session_id: str, query: str) -> RunResult:
    """
    Runs the agent asynchronously, prints CLI-friendly output, and returns a structured RunResult.
    Interaction history persistence should be handled via ToolContext tools (memory agent),
    not via DatabaseSessionService internals in this ADK version.
    """
    content = types.Content(role="user", parts=[types.Part(text=query)])

    print_query_banner(query)
    await display_state(
        runner.session_service, runner.app_name, user_id, session_id, "State BEFORE processing"
    )

    result = RunResult()

    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            accumulate_result(result, event)

    except Exception as e:
        print_error(f"ERROR during agent run: {e}")

    # If we got a final response, print it
    if result.final_text:
        print_final_response(result.final_text)
    else:
        # Temporary fallback for CLI UX when model does tool-only turns
        try:
            session = await runner.session_service.get_session(
                app_name=runner.app_name, user_id=user_id, session_id=session_id
            )
            user_name = session.state.get("user_name")
            if user_name:
                result.final_text = (
                    f"Nice to meet you, {user_name}! What kind of movie are you in the mood for tonight?"
                )
                print_final_response(result.final_text)
        except Exception as e:
            print_error(f"ERROR generating fallback response: {e}")

    await display_state(
        runner.session_service, runner.app_name, user_id, session_id, "State AFTER processing"
    )

    print(f"{Colors.YELLOW}{'-' * 30}{Colors.RESET}")
    return result

