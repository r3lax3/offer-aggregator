from pydantic_settings import BaseSettings


class FilterServiceSettings(BaseSettings):
    model_config = {"env_prefix": ""}

    ANTHROPIC_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379/0"
