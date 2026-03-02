import os
import sys
import re

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

load_dotenv()

console = Console()

SESSION_NAME = "aggregator"


def load_lines(filepath: str) -> list[str]:
    """Load non-empty, non-comment lines from a text file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def build_keyword_pattern(keywords: list[str]) -> re.Pattern | None:
    """Build a compiled regex pattern that matches any of the keywords (case-insensitive)."""
    if not keywords:
        return None
    escaped = [re.escape(kw) for kw in keywords]
    return re.compile("|".join(escaped), re.IGNORECASE)


def display_startup(keywords: list[str], target_chat_id: int, target_name: str, target_link: str | None):
    """Show a pretty startup banner with current configuration."""
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]Telegram Offer Aggregator[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()

    # Keywords table
    kw_table = Table(title="Keywords", show_lines=False, border_style="green")
    kw_table.add_column("#", style="dim", width=4)
    kw_table.add_column("Keyword", style="bold green")
    for i, kw in enumerate(keywords, 1):
        kw_table.add_row(str(i), kw)
    console.print(kw_table)
    console.print()

    console.print(f"  [bold]Mode:[/bold] [blue]All groups & channels (excluding DMs)[/blue]")
    console.print(f"  [bold]Target:[/bold] [magenta]{target_name}[/magenta] [dim](ID: {target_chat_id})[/dim]")
    if target_link:
        console.print(f"  [bold]Invite link:[/bold] [underline cyan]{target_link}[/underline cyan]")
    console.print()


def format_forward_message(message, source_name: str) -> str:
    """Format a message for forwarding to the target chat."""
    header = f"📢 <b>From:</b> <b>{source_name}</b>"
    link = ""
    if hasattr(message.peer_id, "channel_id"):
        link = f"\n🔗 <a href=\"https://t.me/c/{message.peer_id.channel_id}/{message.id}\">Go to message</a>"
    return f"{header}{link}\n\n{message.text}"


async def main():
    # --- Load config ---
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")

    if not api_id or not api_hash:
        console.print(
            "[bold red]Error:[/bold red] API_ID and API_HASH must be set in .env file.\n"
            "Get them at https://my.telegram.org/apps"
        )
        sys.exit(1)

    keywords = load_lines("keywords.txt")
    if not keywords:
        console.print("[bold red]Error:[/bold red] No keywords found in keywords.txt")
        sys.exit(1)

    pattern = build_keyword_pattern(keywords)

    # --- Create session ---
    client = TelegramClient(SESSION_NAME, int(api_id), api_hash)
    await client.start()

    console.print("[green]✓ Session created successfully[/green]")

    # --- Target chat ---
    target_chat_id_env = os.getenv("TARGET_CHAT_ID")
    if target_chat_id_env:
        target_chat_id = int(target_chat_id_env)
    else:
        console.print()
        target_chat_id = int(
            Prompt.ask(
                "[bold]Enter the target chat/channel ID for forwarding matches[/bold]"
            )
        )

    # --- Resolve target chat info ---
    target_entity = await client.get_entity(target_chat_id)
    target_name = getattr(target_entity, "title", None) or getattr(target_entity, "username", None) or "Unknown"
    target_link = None
    if hasattr(target_entity, "username") and target_entity.username:
        target_link = f"https://t.me/{target_entity.username}"
    else:
        try:
            from telethon.tl.functions.messages import ExportChatInviteRequest
            result = await client(ExportChatInviteRequest(target_chat_id))
            target_link = result.link
        except Exception:
            pass

    # --- Display config ---
    display_startup(keywords, target_chat_id, target_name, target_link)

    # --- Set up handler (all messages except DMs) ---
    @client.on(events.NewMessage())
    async def handler(event):
        # Skip direct messages (private chats)
        if isinstance(event.message.peer_id, PeerUser):
            return
        if not event.message.text:
            return
        if not pattern.search(event.message.text):
            return

        chat = await event.get_chat()
        source_name = getattr(chat, "title", None) or getattr(chat, "username", "Unknown")
        text = format_forward_message(event.message, source_name)

        try:
            await client.send_message(target_chat_id, text, parse_mode="html")
            console.print(
                f"  [green]→[/green] Forwarded from [cyan]{source_name}[/cyan]: "
                f"{event.message.text[:80]}..."
            )
        except Exception as e:
            console.print(f"  [red]✗ Forward failed: {e}[/red]")

    console.print("[bold green]▶ Listening for messages... (Ctrl+C to stop)[/bold green]")
    console.print()

    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
