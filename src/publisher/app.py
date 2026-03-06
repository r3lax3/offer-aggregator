from __future__ import annotations

import asyncio

import structlog
from dishka import make_async_container

from shared.broker import RedisMessageBroker
from publisher.container import PublisherProvider
from publisher.bot import PublisherBot

logger = structlog.get_logger()


async def main() -> None:
    container = make_async_container(PublisherProvider())

    broker = await container.get(RedisMessageBroker)
    await broker.ensure_groups()

    publisher = await container.get(PublisherBot)

    logger.info("publisher_service_started")
    await publisher.run()

    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
