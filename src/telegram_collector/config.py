from pydantic_settings import BaseSettings


class TelegramCollectorSettings(BaseSettings):
    model_config = {"env_prefix": ""}

    TG_API_ID: int
    TG_API_HASH: str
    TG_FOLDER_ID: int | None = None
    REDIS_URL: str = "redis://localhost:6379/0"
