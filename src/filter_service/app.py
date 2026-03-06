from __future__ import annotations

import asyncio

import structlog
from dishka import make_async_container

from shared.broker import RedisMessageBroker
from filter_service.container import FilterServiceProvider
from filter_service.pipeline import FilterPipeline

logger = structlog.get_logger()


async def main() -> None:
    container = make_async_container(FilterServiceProvider())

    broker = await container.get(RedisMessageBroker)
    await broker.ensure_groups()

    pipeline = await container.get(FilterPipeline)

    logger.info("filter_service_started")
    await pipeline.run()

    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
