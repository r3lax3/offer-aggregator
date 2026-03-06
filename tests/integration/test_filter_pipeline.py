from unittest.mock import AsyncMock, MagicMock

import pytest
import fakeredis.aioredis

from filter_service.classifier import Classifier
from filter_service.keyword_filter import KeywordFilter
from filter_service.pipeline import FilterPipeline
from shared.broker import RedisMessageBroker
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


@pytest.fixture
def keyword_filter():
    return KeywordFilter(["python", "парсер", "telegram bot", "developer", "freelance"])


def _make_raw(text: str, source: MessageSource = MessageSource.TELEGRAM) -> RawMessage:
    return RawMessage(
        source=source,
        source_id="1",
        chat_id="-100",
        chat_title="Test Chat",
        author="user",
        text=text,
    )


@pytest.mark.integration
class TestFilterPipeline:
    async def test_message_passes_both_stages(self, broker, keyword_filter):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=True)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw("Need a python developer for my project")

        result = await pipeline.process(msg)

        assert result is not None
        assert isinstance(result, FilteredMessage)
        assert "python" in [k.lower() for k in result.matched_keywords]
        classifier.classify.assert_called_once()

    async def test_message_rejected_by_keywords(self, broker, keyword_filter):
        classifier = AsyncMock(spec=Classifier)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw("Nice weather today, isn't it?")

        result = await pipeline.process(msg)

        assert result is None
        classifier.classify.assert_not_called()

    async def test_message_rejected_by_llm(self, broker, keyword_filter):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=False)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw("I just learned python decorators today")

        result = await pipeline.process(msg)

        assert result is None
        classifier.classify.assert_called_once()

    async def test_filtered_message_published_to_stream(self, broker, keyword_filter, redis):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=True)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw("Hiring freelance python developer")

        await pipeline.process(msg)

        from shared.broker import STREAM_FILTERED
        length = await redis.xlen(STREAM_FILTERED)
        assert length == 1

    async def test_rejected_message_not_published(self, broker, keyword_filter, redis):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=False)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw("Just learning python basics")

        await pipeline.process(msg)

        from shared.broker import STREAM_FILTERED
        length = await redis.xlen(STREAM_FILTERED)
        assert length == 0

    async def test_reddit_message_through_pipeline(self, broker, keyword_filter):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=True)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)
        msg = _make_raw(
            "[Hiring] Need a python developer for web scraping",
            source=MessageSource.REDDIT,
        )

        result = await pipeline.process(msg)

        assert result is not None
        assert result.raw.source == MessageSource.REDDIT

    async def test_end_to_end_publish_consume(self, broker, keyword_filter):
        classifier = AsyncMock(spec=Classifier)
        classifier.classify = AsyncMock(return_value=True)

        pipeline = FilterPipeline(broker, keyword_filter, classifier)

        await broker.publish_raw(_make_raw("Need python developer ASAP"))
        await broker.publish_raw(_make_raw("Nice weather today"))
        await broker.publish_raw(_make_raw("Hiring freelance парсер specialist"))

        results = []
        processed = 0
        async for raw_msg in broker.consume_raw(
            group="filter-service", consumer="test", block_ms=100
        ):
            result = await pipeline.process(raw_msg)
            if result:
                results.append(result)
            processed += 1
            if processed >= 3:
                break

        assert len(results) == 2
