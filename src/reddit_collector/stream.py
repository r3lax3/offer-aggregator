from __future__ import annotations

import asyncio
from typing import Any

import structlog

from shared.broker import RedisMessageBroker
from shared.models import MessageSource, RawMessage

logger = structlog.get_logger()


class _StreamExhausted(Exception):
    pass


def _next_submission(stream_iter: Any) -> Any:
    try:
        return next(stream_iter)
    except StopIteration:
        raise _StreamExhausted


class RedditStream:
    def __init__(
        self,
        reddit: Any,
        broker: RedisMessageBroker,
        subreddits: list[str],
    ) -> None:
        self._reddit = reddit
        self._broker = broker
        self._subreddits = subreddits

    def _create_stream(self) -> Any:
        combined = "+".join(self._subreddits)
        subreddit = self._reddit.subreddit(combined)
        return subreddit.stream.submissions(skip_existing=True)

    async def run(self) -> None:
        if not self._subreddits:
            logger.warning("no_subreddits_configured")
            return

        stream = self._create_stream()
        logger.info("reddit_stream_started", subreddits=self._subreddits)

        while True:
            try:
                submission = await asyncio.to_thread(_next_submission, stream)
                text = f"{submission.title}\n{submission.selftext or ''}"

                raw = RawMessage(
                    source=MessageSource.REDDIT,
                    source_id=str(submission.id),
                    chat_id=f"r/{submission.subreddit.display_name}",
                    chat_title=f"r/{submission.subreddit.display_name}",
                    author=f"u/{submission.author.name}" if submission.author else "[deleted]",
                    text=text.strip(),
                    url=f"https://reddit.com{submission.permalink}",
                    context=[],
                )

                await self._broker.publish_raw(raw)
                logger.info(
                    "published_reddit_submission",
                    subreddit=raw.chat_title,
                    submission_id=submission.id,
                )
            except _StreamExhausted:
                await asyncio.sleep(1)
            except Exception:
                logger.exception("reddit_stream_error")
                await asyncio.sleep(30)
                stream = self._create_stream()
