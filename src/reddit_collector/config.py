from pydantic_settings import BaseSettings


class RedditCollectorSettings(BaseSettings):
    model_config = {"env_prefix": ""}

    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str = "offer-aggregator/1.0"
    REDIS_URL: str = "redis://localhost:6379/0"
