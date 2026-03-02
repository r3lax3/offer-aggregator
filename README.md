# Telegram Offer Aggregator

Userbot that monitors Telegram channels/chats for messages matching your keywords and forwards them to a target chat.

## Setup

1. Get API credentials at https://my.telegram.org/apps
2. Copy `.env.example` to `.env` and fill in `API_ID` and `API_HASH`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Add keywords to `keywords.txt` (one per line)
5. Add channels/chats to `channels.txt` (one per line — `@username` or numeric ID)

## Usage

```bash
python bot.py
```

On first run Telethon will ask for your phone number and auth code to create a session. After that the bot will display active keywords and monitored channels, then start listening.

You can set `TARGET_CHAT_ID` in `.env` or enter it interactively on each startup.
