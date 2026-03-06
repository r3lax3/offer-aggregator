from __future__ import annotations

from shared.models import FilteredMessage, MessageSource


def format_message(msg: FilteredMessage) -> str:
    raw = msg.raw
    keywords_str = ", ".join(msg.matched_keywords[:5])

    if raw.source == MessageSource.TELEGRAM:
        return _format_telegram(raw.chat_title, raw.author, raw.text, raw.url, keywords_str)
    elif raw.source == MessageSource.REDDIT:
        return _format_reddit(raw.chat_title, raw.author, raw.text, raw.url, keywords_str)
    return raw.text


def _format_telegram(
    chat_title: str, author: str, text: str, url: str, keywords: str
) -> str:
    parts = [
        f"<b>Telegram | {_escape(chat_title)}</b>",
    ]
    if author:
        parts.append(f"Author: {_escape(author)}")
    if url:
        parts.append(f'<a href="{url}">Go to message</a>')
    parts.append("")
    parts.append(_escape(text[:1500]))
    if keywords:
        parts.append(f"\nKeywords: <i>{_escape(keywords)}</i>")
    return "\n".join(parts)


def _format_reddit(
    chat_title: str, author: str, text: str, url: str, keywords: str
) -> str:
    parts = [
        f"<b>Reddit | {_escape(chat_title)}</b>",
    ]
    if author:
        parts.append(f"Author: {_escape(author)}")
    if url:
        parts.append(f'<a href="{url}">Open post</a>')
    parts.append("")
    parts.append(_escape(text[:1500]))
    if keywords:
        parts.append(f"\nKeywords: <i>{_escape(keywords)}</i>")
    return "\n".join(parts)


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
