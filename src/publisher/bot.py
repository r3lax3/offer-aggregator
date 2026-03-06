from __future__ import annotations

import structlog
from aiogram import Bot

from shared.broker import RedisMessageBroker
from shared.models import FilteredMessage
from publisher.formatter import format_message

logger = structlog.get_logger()


class PublisherBot:
    def __init__(
        self,
        bot: Bot,
        broker: RedisMessageBroker,
        target_chat_id: int,
    ) -> None:
        self._bot = bot
        self._broker = broker
        self._target_chat_id = target_chat_id

    async def send(self, message: FilteredMessage) -> bool:
        text = format_message(message)
        try:
            await self._bot.send_message(
                self._target_chat_id,
                text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(
                "message_published",
                source=message.raw.source.value,
                chat=message.raw.chat_title,
            )
            return True
        except Exception:
            logger.exception("publish_failed", chat=message.raw.chat_title)
            return False

    async def run(self) -> None:
        logger.info("publisher_started", target=self._target_chat_id)
        async for message in self._broker.consume_filtered(
            group="publisher", consumer="bot-1"
        ):
            await self.send(message)
