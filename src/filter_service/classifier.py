from __future__ import annotations

from pathlib import Path
from typing import Protocol

import structlog
from anthropic import AsyncAnthropic

from shared.models import RawMessage

logger = structlog.get_logger()

_PROMPT_FILE = Path(__file__).parent.parent.parent / "config" / "system_prompt.txt"
SYSTEM_PROMPT = _PROMPT_FILE.read_text(encoding="utf-8").strip()


class Classifier(Protocol):
    async def classify(self, message: RawMessage) -> bool: ...


class AnthropicClassifier:
    def __init__(self, client: AsyncAnthropic) -> None:
        self._client = client

    async def classify(self, message: RawMessage) -> bool:
        context_block = ""
        if message.context:
            lines = "\n".join(
                f"{i + 1}. {msg}" for i, msg in enumerate(message.context)
            )
            context_block = f"Recent context messages from this chat:\n{lines}\n\n"

        user_content = (
            f"{context_block}"
            f"Source: {message.source.value} | {message.chat_title}\n"
            f"Author: {message.author}\n\n"
            f"Message to classify:\n{message.text}"
        )

        try:
            response = await self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=3,
                temperature=0,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            answer = response.content[0].text.strip().upper()
            return answer.startswith("YES")
        except Exception:
            logger.exception("llm_classification_failed")
            return True
