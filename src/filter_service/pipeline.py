from __future__ import annotations

import structlog

from shared.broker import RedisMessageBroker
from shared.models import FilteredMessage, RawMessage
from filter_service.classifier import Classifier
from filter_service.keyword_filter import KeywordFilter

logger = structlog.get_logger()


class FilterPipeline:
    def __init__(
        self,
        broker: RedisMessageBroker,
        keyword_filter: KeywordFilter,
        classifier: Classifier,
    ) -> None:
        self._broker = broker
        self._keyword_filter = keyword_filter
        self._classifier = classifier

    async def process(self, message: RawMessage) -> FilteredMessage | None:
        matched = self._keyword_filter.match(message.text)
        if not matched:
            logger.debug("keyword_filter_rejected", chat=message.chat_title)
            return None

        is_offer = await self._classifier.classify(message)
        if not is_offer:
            logger.info(
                "llm_rejected",
                chat=message.chat_title,
                text=message.text[:80],
            )
            return None

        filtered = FilteredMessage(raw=message, matched_keywords=matched)
        await self._broker.publish_filtered(filtered)
        logger.info(
            "message_accepted",
            chat=message.chat_title,
            keywords=matched,
        )
        return filtered

    async def run(self) -> None:
        logger.info("filter_pipeline_started")
        async for message in self._broker.consume_raw(
            group="filter-service", consumer="worker-1"
        ):
            await self.process(message)
