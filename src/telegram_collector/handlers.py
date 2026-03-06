from __future__ import annotations

import structlog

from shared.broker import RedisMessageBroker
from shared.models import MessageSource, RawMessage
from telegram_collector.context_buffer import ContextBuffer

logger = structlog.get_logger()


class TelegramMessageHandler:
    def __init__(
        self,
        broker: RedisMessageBroker,
        context_buffer: ContextBuffer,
    ) -> None:
        self._broker = broker
        self._context = context_buffer

    async def handle(
        self,
        chat_id: int,
        message_id: int,
        chat_title: str,
        author: str,
        text: str,
        is_private: bool,
    ) -> bool:
        if is_private:
            return False
        if not text:
            return False

        chat_key = str(chat_id)
        context = self._context.get_context(chat_key)
        self._context.add(chat_key, text)

        channel_id = abs(chat_id)
        url = f"https://t.me/c/{channel_id}/{message_id}"

        raw = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id=str(message_id),
            chat_id=chat_key,
            chat_title=chat_title,
            author=author,
            text=text,
            url=url,
            context=context,
        )

        await self._broker.publish_raw(raw)
        logger.info("published_telegram_message", chat=chat_title, msg_id=message_id)
        return True
