from pydantic_settings import BaseSettings


class PublisherSettings(BaseSettings):
    model_config = {"env_prefix": ""}

    PUBLISHER_BOT_TOKEN: str
    PUBLISHER_TARGET_CHAT_ID: int
    REDIS_URL: str = "redis://localhost:6379/0"
