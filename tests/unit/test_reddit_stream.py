import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reddit_collector.stream import RedditStream, _StreamExhausted
from shared.models import MessageSource


def _make_submission(
    sub_id: str = "abc",
    title: str = "Test Post",
    selftext: str = "Post body",
    subreddit_name: str = "forhire",
    author_name: str = "poster",
    permalink: str = "/r/forhire/comments/abc/test",
) -> MagicMock:
    sub = MagicMock()
    sub.id = sub_id
    sub.title = title
    sub.selftext = selftext
    sub.subreddit.display_name = subreddit_name
    sub.author.name = author_name
    sub.permalink = permalink
    return sub


def _setup_reddit_mock(reddit: MagicMock) -> MagicMock:
    subreddit_mock = MagicMock()
    stream_mock = MagicMock()
    subreddit_mock.stream.submissions.return_value = stream_mock
    reddit.subreddit.return_value = subreddit_mock
    return stream_mock


class TestRedditStream:
    async def test_publishes_submission(self):
        broker = AsyncMock()
        reddit = MagicMock()
        submission = _make_submission()
        _setup_reddit_mock(reddit)

        call_count = 0

        def fake_next(stream_iter):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return submission
            raise _StreamExhausted

        stream = RedditStream(reddit, broker, ["forhire"])

        with patch("reddit_collector.stream._next_submission", side_effect=fake_next):
            with patch("reddit_collector.stream.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
                sleep_mock.side_effect = asyncio.CancelledError()
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        broker.publish_raw.assert_called_once()
        msg = broker.publish_raw.call_args[0][0]
        assert msg.source == MessageSource.REDDIT
        assert msg.chat_title == "r/forhire"
        assert "Test Post" in msg.text

    async def test_empty_subreddits(self):
        broker = AsyncMock()
        reddit = MagicMock()
        stream = RedditStream(reddit, broker, [])
        await stream.run()
        broker.publish_raw.assert_not_called()

    async def test_combines_subreddits(self):
        broker = AsyncMock()
        reddit = MagicMock()
        _setup_reddit_mock(reddit)

        stream = RedditStream(reddit, broker, ["forhire", "slavelabour", "webscraping"])

        with patch("reddit_collector.stream._next_submission", side_effect=_StreamExhausted):
            with patch("reddit_collector.stream.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
                sleep_mock.side_effect = asyncio.CancelledError()
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        reddit.subreddit.assert_called_with("forhire+slavelabour+webscraping")

    async def test_deleted_author_handled(self):
        broker = AsyncMock()
        reddit = MagicMock()
        submission = _make_submission()
        submission.author = None
        _setup_reddit_mock(reddit)

        call_count = 0

        def fake_next(stream_iter):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return submission
            raise _StreamExhausted

        stream = RedditStream(reddit, broker, ["forhire"])

        with patch("reddit_collector.stream._next_submission", side_effect=fake_next):
            with patch("reddit_collector.stream.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
                sleep_mock.side_effect = asyncio.CancelledError()
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        msg = broker.publish_raw.call_args[0][0]
        assert msg.author == "[deleted]"

    async def test_url_format(self):
        broker = AsyncMock()
        reddit = MagicMock()
        submission = _make_submission(permalink="/r/forhire/comments/xyz/hiring_dev")
        _setup_reddit_mock(reddit)

        call_count = 0

        def fake_next(stream_iter):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return submission
            raise _StreamExhausted

        stream = RedditStream(reddit, broker, ["forhire"])

        with patch("reddit_collector.stream._next_submission", side_effect=fake_next):
            with patch("reddit_collector.stream.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
                sleep_mock.side_effect = asyncio.CancelledError()
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        msg = broker.publish_raw.call_args[0][0]
        assert msg.url == "https://reddit.com/r/forhire/comments/xyz/hiring_dev"

    async def test_no_context_for_reddit(self):
        broker = AsyncMock()
        reddit = MagicMock()
        submission = _make_submission()
        _setup_reddit_mock(reddit)

        call_count = 0

        def fake_next(stream_iter):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return submission
            raise _StreamExhausted

        stream = RedditStream(reddit, broker, ["forhire"])

        with patch("reddit_collector.stream._next_submission", side_effect=fake_next):
            with patch("reddit_collector.stream.asyncio.sleep", new_callable=AsyncMock) as sleep_mock:
                sleep_mock.side_effect = asyncio.CancelledError()
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        msg = broker.publish_raw.call_args[0][0]
        assert msg.context == []

    async def test_reconnects_on_error(self):
        broker = AsyncMock()
        reddit = MagicMock()
        _setup_reddit_mock(reddit)

        call_count = 0

        def fake_next(stream_iter):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Lost connection")
            raise _StreamExhausted

        stream = RedditStream(reddit, broker, ["forhire"])

        sleep_call_count = 0

        async def fake_sleep(seconds):
            nonlocal sleep_call_count
            sleep_call_count += 1
            if sleep_call_count >= 2:
                raise asyncio.CancelledError()

        with patch("reddit_collector.stream._next_submission", side_effect=fake_next):
            with patch("reddit_collector.stream.asyncio.sleep", side_effect=fake_sleep):
                with pytest.raises(asyncio.CancelledError):
                    await stream.run()

        assert reddit.subreddit.call_count >= 2
