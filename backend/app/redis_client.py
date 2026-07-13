from redis.asyncio import ConnectionPool, Redis

from app.config import settings

# A shared connection pool keeps a small, bounded number of connections open
# to Redis even under many concurrent requests, instead of one per request.
_pool = ConnectionPool.from_url(settings.REDIS_URL, max_connections=50, decode_responses=True)


def get_redis() -> Redis:
    return Redis(connection_pool=_pool)
