# utils/console.py

class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"


def print_query_banner(query: str) -> None:
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}"
        f"--- Running Query: {query} ---"
        f"{Colors.RESET}"
    )


def print_final_response(final_text: str) -> None:
    print(
        f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
        f"╔══ AGENT RESPONSE ═════════════════════════════════════════"
        f"{Colors.RESET}"
    )
    print(f"{Colors.CYAN}{Colors.BOLD}{final_text}{Colors.RESET}")
    print(
        f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
        f"╚═════════════════════════════════════════════════════════════"
        f"{Colors.RESET}\n"
    )


def print_error(msg: str) -> None:
    print(f"{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}{msg}{Colors.RESET}")
