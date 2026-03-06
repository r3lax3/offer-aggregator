import asyncio

import pytest
import fakeredis.aioredis

from shared.broker import (
    STREAM_FILTERED,
    STREAM_RAW,
    RedisMessageBroker,
)
from shared.models import FilteredMessage, MessageSource, RawMessage


@pytest.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=False)
    yield r
    await r.aclose()


@pytest.fixture
async def broker(redis):
    b = RedisMessageBroker(redis)
    await b.ensure_groups()
    return b


class TestRedisMessageBroker:
    async def test_ensure_groups_creates_streams(self, redis, broker):
        groups_raw = await redis.xinfo_groups(STREAM_RAW)
        groups_filtered = await redis.xinfo_groups(STREAM_FILTERED)

        def _get_name(g: dict) -> str:
            for key in (b"name", "name"):
                if key in g:
                    val = g[key]
                    return val.decode() if isinstance(val, bytes) else val
            return ""

        raw_names = [_get_name(g) for g in groups_raw]
        filtered_names = [_get_name(g) for g in groups_filtered]
        assert "filter-service" in raw_names
        assert "publisher" in filtered_names

    async def test_ensure_groups_idempotent(self, broker):
        await broker.ensure_groups()
        await broker.ensure_groups()

    async def test_publish_raw(self, redis, broker):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="1",
            chat_id="-100",
            chat_title="test",
            text="hello",
        )
        await broker.publish_raw(msg)
        length = await redis.xlen(STREAM_RAW)
        assert length == 1

    async def test_publish_filtered(self, redis, broker):
        raw = RawMessage(
            source=MessageSource.REDDIT,
            source_id="abc",
            chat_id="r/test",
            chat_title="r/test",
            text="need dev",
        )
        filtered = FilteredMessage(raw=raw, matched_keywords=["dev"])
        await broker.publish_filtered(filtered)
        length = await redis.xlen(STREAM_FILTERED)
        assert length == 1

    async def test_publish_and_consume_raw(self, broker):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="42",
            chat_id="-100",
            chat_title="Dev Chat",
            text="Need a parser for website",
            context=["prev msg"],
        )
        await broker.publish_raw(msg)

        consumed = []
        async for received in broker.consume_raw(
            group="filter-service", consumer="w1", block_ms=100
        ):
            consumed.append(received)
            if len(consumed) >= 1:
                break

        assert len(consumed) == 1
        assert consumed[0].text == "Need a parser for website"
        assert consumed[0].source == MessageSource.TELEGRAM
        assert consumed[0].context == ["prev msg"]

    async def test_publish_and_consume_filtered(self, broker):
        raw = RawMessage(
            source=MessageSource.REDDIT,
            source_id="r1",
            chat_id="r/forhire",
            chat_title="r/forhire",
            text="[Hiring] Python developer needed",
        )
        filtered = FilteredMessage(raw=raw, matched_keywords=["python", "developer"])
        await broker.publish_filtered(filtered)

        consumed = []
        async for received in broker.consume_filtered(
            group="publisher", consumer="b1", block_ms=100
        ):
            consumed.append(received)
            if len(consumed) >= 1:
                break

        assert len(consumed) == 1
        assert consumed[0].raw.text == "[Hiring] Python developer needed"
        assert consumed[0].matched_keywords == ["python", "developer"]

    async def test_consume_multiple_messages_ordered(self, broker):
        for i in range(3):
            msg = RawMessage(
                source=MessageSource.TELEGRAM,
                source_id=str(i),
                chat_id="-100",
                chat_title="test",
                text=f"message {i}",
            )
            await broker.publish_raw(msg)

        consumed = []
        async for received in broker.consume_raw(
            group="filter-service", consumer="w1", block_ms=100
        ):
            consumed.append(received)
            if len(consumed) >= 3:
                break

        assert [m.text for m in consumed] == ["message 0", "message 1", "message 2"]

    async def test_message_acknowledged_not_redelivered(self, redis, broker):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="1",
            chat_id="-100",
            chat_title="test",
            text="ack test",
        )
        await broker.publish_raw(msg)

        async for _ in broker.consume_raw(
            group="filter-service", consumer="w1", block_ms=100
        ):
            break

        pending = await redis.xpending(STREAM_RAW, "filter-service")
        assert pending["pending"] == 0
