from unittest.mock import AsyncMock, MagicMock

import pytest

from filter_service.classifier import SYSTEM_PROMPT, AnthropicClassifier
from shared.models import MessageSource, RawMessage


def _make_message(text: str, context: list[str] | None = None) -> RawMessage:
    return RawMessage(
        source=MessageSource.TELEGRAM,
        source_id="1",
        chat_id="-100",
        chat_title="Dev Chat",
        author="user1",
        text=text,
        context=context or [],
    )


def _mock_client(response_text: str) -> AsyncMock:
    client = AsyncMock()
    content_block = MagicMock()
    content_block.text = response_text
    response = MagicMock()
    response.content = [content_block]
    client.messages.create = AsyncMock(return_value=response)
    return client


class TestAnthropicClassifier:
    async def test_classify_yes(self):
        client = _mock_client("YES")
        classifier = AnthropicClassifier(client)
        msg = _make_message("Need a python developer for parsing project")
        result = await classifier.classify(msg)
        assert result is True

    async def test_classify_no(self):
        client = _mock_client("NO")
        classifier = AnthropicClassifier(client)
        msg = _make_message("Just learned about python decorators today")
        result = await classifier.classify(msg)
        assert result is False

    async def test_classify_yes_with_whitespace(self):
        client = _mock_client("  YES  ")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test")
        result = await classifier.classify(msg)
        assert result is True

    async def test_classify_case_insensitive_response(self):
        client = _mock_client("yes")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test")
        result = await classifier.classify(msg)
        assert result is True

    async def test_fail_open_on_api_error(self):
        client = AsyncMock()
        client.messages.create = AsyncMock(side_effect=Exception("API error"))
        classifier = AnthropicClassifier(client)
        msg = _make_message("test message")
        result = await classifier.classify(msg)
        assert result is True

    async def test_context_included_in_request(self):
        client = _mock_client("YES")
        classifier = AnthropicClassifier(client)
        msg = _make_message(
            "How much for the bot?",
            context=["Hi everyone", "Anyone know a bot developer?"],
        )
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "Hi everyone" in user_msg
        assert "Anyone know a bot developer?" in user_msg

    async def test_uses_haiku_model(self):
        client = _mock_client("YES")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test")
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        assert "haiku" in call_args.kwargs["model"]

    async def test_max_tokens_minimal(self):
        client = _mock_client("NO")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test")
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        assert call_args.kwargs["max_tokens"] <= 10

    async def test_system_prompt_set(self):
        client = _mock_client("NO")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test")
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        assert call_args.kwargs["system"] == SYSTEM_PROMPT

    async def test_source_info_in_request(self):
        client = _mock_client("YES")
        classifier = AnthropicClassifier(client)
        msg = RawMessage(
            source=MessageSource.REDDIT,
            source_id="abc",
            chat_id="r/forhire",
            chat_title="r/forhire",
            author="u/poster",
            text="[Hiring] need scraper",
        )
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "reddit" in user_msg.lower()
        assert "r/forhire" in user_msg

    async def test_no_context_block_when_empty(self):
        client = _mock_client("YES")
        classifier = AnthropicClassifier(client)
        msg = _make_message("test", context=[])
        await classifier.classify(msg)

        call_args = client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "Recent context" not in user_msg
