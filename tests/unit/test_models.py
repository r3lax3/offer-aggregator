from datetime import datetime

import pytest

from shared.models import FilteredMessage, MessageSource, RawMessage


class TestRawMessage:
    def test_create_telegram_message(self):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="123",
            chat_id="-100456",
            chat_title="Dev Chat",
            author="user1",
            text="Looking for a python developer",
            url="https://t.me/c/456/123",
        )
        assert msg.source == MessageSource.TELEGRAM
        assert msg.source_id == "123"
        assert msg.chat_title == "Dev Chat"
        assert msg.text == "Looking for a python developer"
        assert msg.context == []

    def test_create_reddit_message(self):
        msg = RawMessage(
            source=MessageSource.REDDIT,
            source_id="abc123",
            chat_id="r/forhire",
            chat_title="r/forhire",
            author="u/poster",
            text="[Hiring] Need a web scraper",
            url="https://reddit.com/r/forhire/comments/abc123",
        )
        assert msg.source == MessageSource.REDDIT
        assert msg.author == "u/poster"

    def test_default_timestamp(self):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="1",
            chat_id="1",
            chat_title="test",
            text="test",
        )
        assert isinstance(msg.timestamp, datetime)

    def test_context_preserved(self):
        ctx = ["msg1", "msg2", "msg3"]
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="1",
            chat_id="1",
            chat_title="test",
            text="test",
            context=ctx,
        )
        assert msg.context == ctx
        assert len(msg.context) == 3

    def test_serialization_roundtrip(self):
        msg = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="42",
            chat_id="-100999",
            chat_title="Test Chat",
            author="alice",
            text="Need a parser",
            url="https://t.me/c/999/42",
            context=["prev1", "prev2"],
        )
        json_str = msg.model_dump_json()
        restored = RawMessage.model_validate_json(json_str)
        assert restored.source == msg.source
        assert restored.text == msg.text
        assert restored.context == msg.context
        assert restored.url == msg.url

    def test_empty_optional_fields(self):
        msg = RawMessage(
            source=MessageSource.REDDIT,
            source_id="1",
            chat_id="r/test",
            chat_title="r/test",
            text="hello",
        )
        assert msg.author == ""
        assert msg.url == ""
        assert msg.context == []


class TestFilteredMessage:
    def test_create_filtered_message(self):
        raw = RawMessage(
            source=MessageSource.TELEGRAM,
            source_id="1",
            chat_id="1",
            chat_title="test",
            text="Need python developer",
        )
        filtered = FilteredMessage(
            raw=raw,
            matched_keywords=["python", "developer"],
        )
        assert filtered.raw.text == "Need python developer"
        assert filtered.matched_keywords == ["python", "developer"]

    def test_serialization_roundtrip(self):
        raw = RawMessage(
            source=MessageSource.REDDIT,
            source_id="abc",
            chat_id="r/forhire",
            chat_title="r/forhire",
            text="[Hiring] Bot dev",
            context=["context1"],
        )
        filtered = FilteredMessage(
            raw=raw,
            matched_keywords=["bot"],
            confidence="high",
        )
        json_str = filtered.model_dump_json()
        restored = FilteredMessage.model_validate_json(json_str)
        assert restored.raw.source == MessageSource.REDDIT
        assert restored.matched_keywords == ["bot"]
        assert restored.confidence == "high"


class TestMessageSource:
    def test_telegram_value(self):
        assert MessageSource.TELEGRAM == "telegram"

    def test_reddit_value(self):
        assert MessageSource.REDDIT == "reddit"

    def test_string_comparison(self):
        assert MessageSource.TELEGRAM == "telegram"
        assert MessageSource("reddit") == MessageSource.REDDIT
