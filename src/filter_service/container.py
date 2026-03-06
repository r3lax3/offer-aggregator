from anthropic import AsyncAnthropic
from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from shared.broker import RedisMessageBroker
from shared.config import load_lines
from filter_service.classifier import AnthropicClassifier, Classifier
from filter_service.config import FilterServiceSettings
from filter_service.keyword_filter import KeywordFilter
from filter_service.pipeline import FilterPipeline


class FilterServiceProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> FilterServiceSettings:
        return FilterServiceSettings()

    @provide(scope=Scope.APP)
    def redis(self, settings: FilterServiceSettings) -> Redis:
        return Redis.from_url(settings.REDIS_URL, decode_responses=False)

    @provide(scope=Scope.APP)
    def broker(self, redis: Redis) -> RedisMessageBroker:
        return RedisMessageBroker(redis)

    @provide(scope=Scope.APP)
    def anthropic_client(self, settings: FilterServiceSettings) -> AsyncAnthropic:
        return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    @provide(scope=Scope.APP)
    def classifier(self, client: AsyncAnthropic) -> Classifier:
        return AnthropicClassifier(client)

    @provide(scope=Scope.APP)
    def keyword_filter(self) -> KeywordFilter:
        keywords = load_lines("config/keywords.txt")
        return KeywordFilter(keywords)

    @provide(scope=Scope.APP)
    def pipeline(
        self,
        broker: RedisMessageBroker,
        keyword_filter: KeywordFilter,
        classifier: Classifier,
    ) -> FilterPipeline:
        return FilterPipeline(broker, keyword_filter, classifier)
