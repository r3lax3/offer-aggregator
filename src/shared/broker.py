from __future__ import annotations

import json
from typing import AsyncIterator, Protocol

from redis.asyncio import Redis

from shared.models import FilteredMessage, RawMessage


STREAM_RAW = "stream:raw_messages"
STREAM_FILTERED = "stream:filtered_messages"


class MessagePublisher(Protocol):
    async def publish_raw(self, message: RawMessage) -> None: ...
    async def publish_filtered(self, message: FilteredMessage) -> None: ...


class MessageConsumer(Protocol):
    async def consume_raw(self, group: str, consumer: str) -> AsyncIterator[RawMessage]: ...
    async def consume_filtered(self, group: str, consumer: str) -> AsyncIterator[FilteredMessage]: ...


class RedisMessageBroker:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def ensure_groups(self) -> None:
        for stream, group in [
            (STREAM_RAW, "filter-service"),
            (STREAM_FILTERED, "publisher"),
        ]:
            try:
                await self._redis.xgroup_create(stream, group, id="0", mkstream=True)
            except Exception:
                pass

    async def publish_raw(self, message: RawMessage) -> None:
        await self._redis.xadd(STREAM_RAW, {"data": message.model_dump_json()})

    async def publish_filtered(self, message: FilteredMessage) -> None:
        await self._redis.xadd(STREAM_FILTERED, {"data": message.model_dump_json()})

    async def consume_raw(
        self, group: str, consumer: str, block_ms: int = 5000
    ) -> AsyncIterator[RawMessage]:
        while True:
            entries = await self._redis.xreadgroup(
                group, consumer, {STREAM_RAW: ">"}, count=1, block=block_ms
            )
            if not entries:
                continue
            for _stream, messages in entries:
                for msg_id, fields in messages:
                    data = json.loads(fields[b"data"])
                    await self._redis.xack(STREAM_RAW, group, msg_id)
                    yield RawMessage(**data)

    async def consume_filtered(
        self, group: str, consumer: str, block_ms: int = 5000
    ) -> AsyncIterator[FilteredMessage]:
        while True:
            entries = await self._redis.xreadgroup(
                group, consumer, {STREAM_FILTERED: ">"}, count=1, block=block_ms
            )
            if not entries:
                continue
            for _stream, messages in entries:
                for msg_id, fields in messages:
                    data = json.loads(fields[b"data"])
                    await self._redis.xack(STREAM_FILTERED, group, msg_id)
                    yield FilteredMessage(**data)
