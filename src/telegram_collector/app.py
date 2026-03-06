from __future__ import annotations

import asyncio

import structlog
from dishka import make_async_container
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser

from shared.broker import RedisMessageBroker
from telegram_collector.config import TelegramCollectorSettings
from telegram_collector.container import TelegramCollectorProvider
from telegram_collector.handlers import TelegramMessageHandler

logger = structlog.get_logger()


async def main() -> None:
    container = make_async_container(TelegramCollectorProvider())

    settings = await container.get(TelegramCollectorSettings)
    broker = await container.get(RedisMessageBroker)
    handler = await container.get(TelegramMessageHandler)

    await broker.ensure_groups()

    client = TelegramClient("aggregator", settings.TG_API_ID, settings.TG_API_HASH)
    await client.start()

    logger.info("telegram_collector_started")

    @client.on(events.NewMessage())
    async def on_message(event: events.NewMessage.Event) -> None:
        is_private = isinstance(event.message.peer_id, PeerUser)
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", None) or getattr(chat, "username", "Unknown")
        sender = await event.get_sender()
        author = ""
        if sender:
            author = getattr(sender, "username", "") or getattr(sender, "first_name", "")

        await handler.handle(
            chat_id=event.message.chat_id,
            message_id=event.message.id,
            chat_title=chat_title,
            author=author,
            text=event.message.text or "",
            is_private=is_private,
        )

    await client.run_until_disconnected()
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
