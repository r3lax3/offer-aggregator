from __future__ import annotations

import re


class KeywordFilter:
    def __init__(self, keywords: list[str]) -> None:
        self._keywords = keywords
        self._pattern: re.Pattern | None = None
        if keywords:
            escaped = [re.escape(kw) for kw in keywords]
            self._pattern = re.compile("|".join(escaped), re.IGNORECASE)

    def match(self, text: str) -> list[str]:
        if not self._pattern:
            return []
        return [m.group() for m in self._pattern.finditer(text)]

    @property
    def keywords(self) -> list[str]:
        return self._keywords.copy()
