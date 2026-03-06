# Offer Aggregator

Multi-service offer aggregator that monitors Telegram chats and Reddit subreddits for potential freelance job opportunities, filters them with keyword matching + LLM classification (Claude Haiku), and publishes relevant offers to a Telegram bot chat.

## Architecture

4 microservices communicating via Redis Streams:

```
telegram-collector ──→ Redis (raw_messages) ──→ filter-service ──→ Redis (filtered_messages) ──→ publisher
reddit-collector  ──↗                                                                            (Aiogram bot)
```

| Service | Role | Tech |
|---------|------|------|
| `telegram-collector` | Telethon userbot, collects messages from groups/channels | Telethon |
| `reddit-collector` | Monitors subreddits via PRAW stream | PRAW |
| `filter-service` | Two-stage filtering: keyword regex + Claude Haiku classification | Anthropic API |
| `publisher` | Posts filtered offers to target Telegram chat | Aiogram |

DI via [Dishka](https://github.com/reagento/dishka). Inter-service communication via Redis Streams with consumer groups.

## Setup

1. Copy `.env.example` to `.env` and fill in credentials
2. Edit `config/keywords.txt` and `config/subreddits.txt`

### Docker (recommended)

```bash
docker compose up -d
```

### Local dev

```bash
pip install -e ".[all]"

# Run each service in a separate terminal:
PYTHONPATH=src python -m telegram_collector.app
PYTHONPATH=src python -m reddit_collector.app
PYTHONPATH=src python -m filter_service.app
PYTHONPATH=src python -m publisher.app
```

## Tests

```bash
pip install -e ".[dev]"
PYTHONPATH=src python -m pytest tests/ -v
```

## Configuration

- `config/keywords.txt` - Keywords for pre-filtering (one per line, `#` for comments)
- `config/subreddits.txt` - Subreddits to monitor (without `r/` prefix)
- `.env` - API credentials (see `.env.example`)
