from __future__ import annotations

from collections import defaultdict, deque


class ContextBuffer:
    def __init__(self, max_size: int = 5) -> None:
        self._max_size = max_size
        self._buffers: dict[str, deque[str]] = defaultdict(
            lambda: deque(maxlen=self._max_size)
        )

    def add(self, chat_id: str, text: str) -> None:
        self._buffers[chat_id].append(text)

    def get_context(self, chat_id: str) -> list[str]:
        return list(self._buffers[chat_id])

    def clear(self, chat_id: str | None = None) -> None:
        if chat_id is None:
            self._buffers.clear()
        else:
            self._buffers.pop(chat_id, None)
