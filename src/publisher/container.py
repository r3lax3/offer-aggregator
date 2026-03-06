from aiogram import Bot
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from shared.broker import RedisMessageBroker
from publisher.bot import PublisherBot
from publisher.config import PublisherSettings


class PublisherProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> PublisherSettings:
        return PublisherSettings()

    @provide(scope=Scope.APP)
    def redis(self, settings: PublisherSettings) -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=False)

    @provide(scope=Scope.APP)
    def broker(self, redis: Redis) -> RedisMessageBroker:
        return RedisMessageBroker(redis)

    @provide(scope=Scope.APP)
    def bot(self, settings: PublisherSettings) -> Bot:
        return Bot(token=settings.PUBLISHER_BOT_TOKEN)

    @provide(scope=Scope.APP)
    def publisher_bot(
        self,
        bot: Bot,
        broker: RedisMessageBroker,
        settings: PublisherSettings,
    ) -> PublisherBot:
        return PublisherBot(bot, broker, settings.PUBLISHER_TARGET_CHAT_ID)
