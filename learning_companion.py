"""
Learning Companion — Powered by Cognee
A CLI study assistant with persistent memory.

Each time you run this, it remembers what you've studied before.
Feed it notes, ask it questions, and watch it get smarter over time.

Usage:
    python learning_companion.py

Commands inside the app:
    study <text>    — Store notes/text into memory
    ask <question>  — Recall answers from memory
    improve         — Enrich the memory graph (run after studying a lot)
    forget          — Wipe all memory (fresh start)
    help            — Show commands
    quit            — Exit
"""

import asyncio
import sys
import cognee

BANNER = """
┌──────────────────────────────────────────┐
│         📚  Learning Companion           │
│         Powered by Cognee Memory         │
└──────────────────────────────────────────┘
Memory persists across sessions — the more you study, the smarter it gets.
"""

HELP_TEXT = """
Commands:
  study <text>    Store notes or text into long-term memory
  ask <question>  Ask a question — answers come from your memory
  improve         Enrich and deepen memory graph connections
  forget          Wipe all memory and start fresh
  help            Show this menu
  quit            Exit
"""


async def do_study(text: str) -> None:
    print("\n⏳  Processing and storing in memory...")
    await cognee.remember(text)
    print("✅  Stored! Memory graph updated.\n")


async def do_ask(question: str) -> None:
    print("\n🔍  Searching memory...\n")
    try:
        results = await cognee.recall(query_text=question)
    except Exception as e:
        print(f"⚠️  Could not search memory: {e}\n")
        return

    if not results:
        print("❌  Nothing found. Try studying some material first with: study <text>\n")
        return

    print("📖  From memory:\n")
    # results is a list of objects with a .text attribute
    seen = set()
    count = 0
    for result in results:
        text = getattr(result, "text", None) or str(result)
        text = text.strip()
        if text and text not in seen:
            seen.add(text)
            count += 1
            print(f"  {count}. {text}\n")
        if count >= 5:
            break

    if count == 0:
        print("  (Memory returned results but no readable text was found.)\n")


async def do_improve() -> None:
    print("\n⏳  Enriching memory graph — this may take a moment...")
    try:
        await cognee.improve()
        print("✅  Memory graph enriched. Connections strengthened.\n")
    except Exception as e:
        print(f"⚠️  Improve failed: {e}\n")


async def do_forget() -> None:
    confirm = input("\n⚠️  This will erase ALL memory. Type 'yes' to confirm: ").strip()
    if confirm.lower() == "yes":
        await cognee.forget(everything=True)
        print("🗑️   Memory cleared. Fresh start!\n")
    else:
        print("Cancelled.\n")


async def main() -> None:
    print(BANNER)
    print(HELP_TEXT)

    while True:
        try:
            raw = input("📚 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Keep learning. 👋")
            sys.exit(0)

        if not raw:
            continue

        parts = raw.split(" ", 1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "study":
            if not arg:
                print("  Usage: study <your notes or text here>\n")
            else:
                await do_study(arg)

        elif cmd == "ask":
            if not arg:
                print("  Usage: ask <your question>\n")
            else:
                await do_ask(arg)

        elif cmd == "improve":
            await do_improve()

        elif cmd == "forget":
            await do_forget()

        elif cmd in ("help", "h", "?"):
            print(HELP_TEXT)

        elif cmd in ("quit", "exit", "q"):
            print("Goodbye! Keep learning. 👋")
            break

        else:
            print(f"  Unknown command '{cmd}'. Type 'help' for options.\n")


if __name__ == "__main__":
    asyncio.run(main())
