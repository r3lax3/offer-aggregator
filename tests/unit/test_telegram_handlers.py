from unittest.mock import AsyncMock

import pytest

from shared.models import MessageSource
from telegram_collector.context_buffer import ContextBuffer
from telegram_collector.handlers import TelegramMessageHandler


@pytest.fixture
def broker():
    b = AsyncMock()
    b.publish_raw = AsyncMock()
    return b


@pytest.fixture
def handler(broker):
    return TelegramMessageHandler(
        broker=broker,
        context_buffer=ContextBuffer(max_size=5),
    )


class TestTelegramMessageHandler:
    async def test_handle_group_message(self, handler, broker):
        result = await handler.handle(
            chat_id=-100456,
            message_id=123,
            chat_title="Dev Chat",
            author="alice",
            text="Need a python developer",
            is_private=False,
        )
        assert result is True
        broker.publish_raw.assert_called_once()
        msg = broker.publish_raw.call_args[0][0]
        assert msg.source == MessageSource.TELEGRAM
        assert msg.text == "Need a python developer"
        assert msg.chat_title == "Dev Chat"

    async def test_skip_private_messages(self, handler, broker):
        result = await handler.handle(
            chat_id=12345,
            message_id=1,
            chat_title="Private",
            author="bob",
            text="hello",
            is_private=True,
        )
        assert result is False
        broker.publish_raw.assert_not_called()

    async def test_skip_empty_text(self, handler, broker):
        result = await handler.handle(
            chat_id=-100456,
            message_id=1,
            chat_title="Dev Chat",
            author="alice",
            text="",
            is_private=False,
        )
        assert result is False
        broker.publish_raw.assert_not_called()

    async def test_context_buffer_populated(self, handler, broker):
        await handler.handle(
            chat_id=-100456,
            message_id=1,
            chat_title="Dev Chat",
            author="alice",
            text="first message",
            is_private=False,
        )
        await handler.handle(
            chat_id=-100456,
            message_id=2,
            chat_title="Dev Chat",
            author="bob",
            text="second message",
            is_private=False,
        )

        second_call_msg = broker.publish_raw.call_args_list[1][0][0]
        assert second_call_msg.context == ["first message"]

    async def test_context_from_different_chats_separated(self, handler, broker):
        await handler.handle(
            chat_id=-100111,
            message_id=1,
            chat_title="Chat A",
            author="a",
            text="chat A msg",
            is_private=False,
        )
        await handler.handle(
            chat_id=-100222,
            message_id=2,
            chat_title="Chat B",
            author="b",
            text="chat B msg",
            is_private=False,
        )

        chat_b_msg = broker.publish_raw.call_args_list[1][0][0]
        assert chat_b_msg.context == []

    async def test_url_format(self, handler, broker):
        await handler.handle(
            chat_id=-100456,
            message_id=789,
            chat_title="Test",
            author="x",
            text="test",
            is_private=False,
        )
        msg = broker.publish_raw.call_args[0][0]
        assert "100456" in msg.url
        assert "789" in msg.url

    async def test_context_limited_to_5(self, handler, broker):
        for i in range(7):
            await handler.handle(
                chat_id=-100456,
                message_id=i,
                chat_title="Test",
                author="x",
                text=f"msg{i}",
                is_private=False,
            )

        last_msg = broker.publish_raw.call_args_list[6][0][0]
        assert len(last_msg.context) == 5
        assert last_msg.context[0] == "msg1"
        assert last_msg.context[4] == "msg5"
