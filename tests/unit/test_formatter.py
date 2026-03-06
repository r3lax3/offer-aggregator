import pytest

from publisher.formatter import format_message, _escape
from shared.models import FilteredMessage, MessageSource, RawMessage


def _make_filtered(
    source: MessageSource = MessageSource.TELEGRAM,
    chat_title: str = "Dev Chat",
    author: str = "alice",
    text: str = "Need a python dev",
    url: str = "https://t.me/c/123/456",
    keywords: list[str] | None = None,
) -> FilteredMessage:
    raw = RawMessage(
        source=source,
        source_id="1",
        chat_id="1",
        chat_title=chat_title,
        author=author,
        text=text,
        url=url,
    )
    return FilteredMessage(
        raw=raw,
        matched_keywords=keywords or ["python"],
    )


class TestFormatter:
    def test_telegram_format_contains_source(self):
        msg = _make_filtered()
        result = format_message(msg)
        assert "Telegram" in result
        assert "Dev Chat" in result

    def test_telegram_format_contains_author(self):
        msg = _make_filtered(author="bob")
        result = format_message(msg)
        assert "bob" in result

    def test_telegram_format_contains_url(self):
        msg = _make_filtered(url="https://t.me/c/123/456")
        result = format_message(msg)
        assert "https://t.me/c/123/456" in result

    def test_telegram_format_contains_text(self):
        msg = _make_filtered(text="Looking for a developer")
        result = format_message(msg)
        assert "Looking for a developer" in result

    def test_telegram_format_contains_keywords(self):
        msg = _make_filtered(keywords=["python", "developer"])
        result = format_message(msg)
        assert "python" in result
        assert "developer" in result

    def test_reddit_format_contains_source(self):
        msg = _make_filtered(
            source=MessageSource.REDDIT,
            chat_title="r/forhire",
            url="https://reddit.com/r/forhire/abc",
        )
        result = format_message(msg)
        assert "Reddit" in result
        assert "r/forhire" in result

    def test_reddit_format_contains_url(self):
        msg = _make_filtered(
            source=MessageSource.REDDIT,
            url="https://reddit.com/r/forhire/abc",
        )
        result = format_message(msg)
        assert "https://reddit.com/r/forhire/abc" in result

    def test_text_truncated_at_1500(self):
        long_text = "a" * 2000
        msg = _make_filtered(text=long_text)
        result = format_message(msg)
        assert "a" * 1500 in result
        assert "a" * 1501 not in result

    def test_html_entities_escaped(self):
        msg = _make_filtered(text="<script>alert('xss')</script>")
        result = format_message(msg)
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_no_author_field_when_empty(self):
        msg = _make_filtered(author="")
        result = format_message(msg)
        assert "Author:" not in result

    def test_max_5_keywords_shown(self):
        msg = _make_filtered(keywords=["a", "b", "c", "d", "e", "f", "g"])
        result = format_message(msg)
        assert "f" not in result or "Keywords" in result


class TestEscape:
    def test_escape_ampersand(self):
        assert _escape("a & b") == "a &amp; b"

    def test_escape_lt_gt(self):
        assert _escape("<b>") == "&lt;b&gt;"

    def test_no_escape_needed(self):
        assert _escape("hello world") == "hello world"
