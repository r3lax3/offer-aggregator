import praw
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from shared.broker import RedisMessageBroker
from shared.config import load_lines
from reddit_collector.config import RedditCollectorSettings
from reddit_collector.stream import RedditStream


class RedditCollectorProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> RedditCollectorSettings:
        return RedditCollectorSettings()

    @provide(scope=Scope.APP)
    def redis(self, settings: RedditCollectorSettings) -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=False)

    @provide(scope=Scope.APP)
    def broker(self, redis: Redis) -> RedisMessageBroker:
        return RedisMessageBroker(redis)

    @provide(scope=Scope.APP)
    def reddit(self, settings: RedditCollectorSettings) -> praw.Reddit:
        return praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT,
        )

    @provide(scope=Scope.APP)
    def subreddits(self) -> list[str]:
        return load_lines("config/subreddits.txt")

    @provide(scope=Scope.APP)
    def stream(
        self,
        reddit: praw.Reddit,
        broker: RedisMessageBroker,
        subreddits: list[str],
    ) -> RedditStream:
        return RedditStream(reddit, broker, subreddits)
