"""
cli.py
------
Terminal / command-line version of the WikiNews Chatbot.
Run with: python cli.py
No browser needed — works entirely in your terminal.
"""

from colorama import init, Fore, Style
from chatbot import Session, respond

init(autoreset=True)


def print_banner():
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════╗
║        📰  WikiNews Chatbot  📰          ║
║   Powered by Wikipedia · Built in Python ║
╚══════════════════════════════════════════╝
""" + Style.RESET_ALL)
    print(Fore.YELLOW + "  Type a topic to get started, or 'help' for commands.")
    print(Fore.YELLOW + "  Type 'quit' or 'exit' to leave.\n" + Style.RESET_ALL)


def print_bot(result: dict):
    msg_type = result.get("type", "info")

    # Title line
    if result.get("title"):
        print(Fore.CYAN + Style.BRIGHT + f"\n  📖  {result['title']}" + Style.RESET_ALL)
        if result.get("url"):
            print(Fore.BLUE + f"  🔗  {result['url']}" + Style.RESET_ALL)

    # Main text
    color = {
        "info":     Fore.WHITE,
        "error":    Fore.RED,
        "greeting": Fore.GREEN,
        "help":     Fore.YELLOW,
        "bye":      Fore.MAGENTA,
    }.get(msg_type, Fore.WHITE)

    print(color + "\n  🤖  " + result["text"] + "\n" + Style.RESET_ALL)

    # Keywords
    if result.get("keywords"):
        kws = "  ".join(f"#{k}" for k in result["keywords"])
        print(Fore.MAGENTA + f"  🔑  {kws}" + Style.RESET_ALL)

    # Alternative results
    if result.get("results"):
        print(Fore.YELLOW + "\n  💡  Related topics you might explore:" + Style.RESET_ALL)
        for i, r in enumerate(result["results"][:3], 1):
            print(Fore.YELLOW + f"     {i}. {r['title']}" + Style.RESET_ALL)

    print(Fore.WHITE + Style.DIM + "  " + "─" * 46 + Style.RESET_ALL)


def main():
    print_banner()
    chat_session = Session()

    while True:
        try:
            user_input = input(Fore.GREEN + Style.BRIGHT + "  You  ➜  " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print(Fore.MAGENTA + "\n\n  Goodbye! 👋\n" + Style.RESET_ALL)
            break

        if not user_input:
            continue

        result = respond(user_input, chat_session)
        print_bot(result)

        if result.get("type") == "bye":
            break


if __name__ == "__main__":
    main()
