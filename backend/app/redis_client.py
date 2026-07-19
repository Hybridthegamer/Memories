from redis.asyncio import BlockingConnectionPool, Redis

from app.config import settings

# A shared connection pool keeps a bounded number of connections open to
# Redis even under many concurrent requests, instead of one per request.
# Explicit socket timeouts matter here: without them, a slow/overloaded
# Redis under heavy traffic would hang requests indefinitely instead of
# failing fast.
#
# Deliberately a *blocking* pool, not a plain one: a plain ConnectionPool
# raises ConnectionError immediately once max_connections is in use, and
# since the rate limiter fails open on any RedisError, a plain pool turns
# "more concurrent requests than the pool's size" into "rate limiting
# silently disables itself" — measured locally (see stress tests), a burst
# of 60 concurrent requests against a pool of 50 let ~10 extra requests
# through the limiter for free. A blocking pool instead makes a caller wait
# briefly for a connection to free up, so ordinary bursts queue for
# milliseconds instead of bypassing the limiter; only a real outage/timeout
# still trips the fail-open path.
_pool = BlockingConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=200,
    timeout=3,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def get_redis() -> Redis:
    return Redis(connection_pool=_pool)
