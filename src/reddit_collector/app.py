from __future__ import annotations

import asyncio

import structlog
from dishka import make_async_container

from shared.broker import RedisMessageBroker
from reddit_collector.container import RedditCollectorProvider
from reddit_collector.stream import RedditStream

logger = structlog.get_logger()


async def main() -> None:
    container = make_async_container(RedditCollectorProvider())

    broker = await container.get(RedisMessageBroker)
    await broker.ensure_groups()

    stream = await container.get(RedditStream)

    logger.info("reddit_collector_started")
    await stream.run()

    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
