from unittest.mock import AsyncMock, MagicMock

import pytest

from publisher.bot import PublisherBot
from shared.models import FilteredMessage, MessageSource, RawMessage


def _make_filtered(text: str = "Need a dev") -> FilteredMessage:
    raw = RawMessage(
        source=MessageSource.TELEGRAM,
        source_id="1",
        chat_id="-100",
        chat_title="Dev Chat",
        author="alice",
        text=text,
        url="https://t.me/c/100/1",
    )
    return FilteredMessage(raw=raw, matched_keywords=["dev"])


class TestPublisherBot:
    async def test_send_success(self):
        bot_mock = AsyncMock()
        bot_mock.send_message = AsyncMock()
        broker_mock = AsyncMock()

        publisher = PublisherBot(
            bot=bot_mock,
            broker=broker_mock,
            target_chat_id=-100999,
        )

        msg = _make_filtered()
        result = await publisher.send(msg)

        assert result is True
        bot_mock.send_message.assert_called_once()
        call_args = bot_mock.send_message.call_args
        assert call_args[0][0] == -100999
        assert "HTML" in str(call_args)

    async def test_send_failure(self):
        bot_mock = AsyncMock()
        bot_mock.send_message = AsyncMock(side_effect=Exception("Network error"))
        broker_mock = AsyncMock()

        publisher = PublisherBot(
            bot=bot_mock,
            broker=broker_mock,
            target_chat_id=-100999,
        )

        msg = _make_filtered()
        result = await publisher.send(msg)

        assert result is False

    async def test_send_formats_html(self):
        bot_mock = AsyncMock()
        bot_mock.send_message = AsyncMock()
        broker_mock = AsyncMock()

        publisher = PublisherBot(
            bot=bot_mock,
            broker=broker_mock,
            target_chat_id=-100999,
        )

        msg = _make_filtered("Need <b>python</b> developer")
        await publisher.send(msg)

        sent_text = bot_mock.send_message.call_args[0][1]
        assert "&lt;b&gt;" in sent_text

    async def test_disable_web_preview(self):
        bot_mock = AsyncMock()
        bot_mock.send_message = AsyncMock()
        broker_mock = AsyncMock()

        publisher = PublisherBot(
            bot=bot_mock,
            broker=broker_mock,
            target_chat_id=-100999,
        )

        await publisher.send(_make_filtered())

        call_kwargs = bot_mock.send_message.call_args[1]
        assert call_kwargs.get("disable_web_page_preview") is True
