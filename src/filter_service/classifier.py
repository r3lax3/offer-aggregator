from __future__ import annotations

from typing import Protocol

import structlog
from anthropic import AsyncAnthropic

from shared.models import RawMessage

logger = structlog.get_logger()

SYSTEM_PROMPT = """\
You are a classifier that determines if a message represents a potential freelance \
job order, hiring post, or project request related to software development.

Consider:
- Is someone looking to hire a developer or pay for work?
- Is this a job posting, project request, or freelance opportunity?
- Does this look like a client seeking services (parsing, bots, automation, web dev, etc.)?

Ignore:
- General discussion, tutorials, news, self-promotion
- Questions about learning or asking for advice
- Someone offering their own services (not hiring)
- Spam, ads for courses or products

Reply with exactly YES or NO. Nothing else.\
"""


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
