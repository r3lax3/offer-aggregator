from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from shared.broker import RedisMessageBroker
from telegram_collector.config import TelegramCollectorSettings
from telegram_collector.context_buffer import ContextBuffer
from telegram_collector.handlers import TelegramMessageHandler


class TelegramCollectorProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> TelegramCollectorSettings:
        return TelegramCollectorSettings()

    @provide(scope=Scope.APP)
    def redis(self, settings: TelegramCollectorSettings) -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=False)

    @provide(scope=Scope.APP)
    def broker(self, redis: Redis) -> RedisMessageBroker:
        return RedisMessageBroker(redis)

    @provide(scope=Scope.APP)
    def context_buffer(self) -> ContextBuffer:
        return ContextBuffer(max_size=5)

    @provide(scope=Scope.APP)
    def handler(
        self,
        broker: RedisMessageBroker,
        context_buffer: ContextBuffer,
    ) -> TelegramMessageHandler:
        return TelegramMessageHandler(broker, context_buffer)
