import logging

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.redis_client import get_redis

logger = logging.getLogger("rate_limit")


def rate_limit_by_ip(key_prefix: str, count: int, window_seconds: int):
    """Fixed-window rate limiter dependency, keyed by client IP.

    Uses Redis INCR + EXPIRE so the check is a couple of cheap round trips
    and stays correct under concurrent requests (INCR is atomic in Redis).
    This is the primary identity signal available now that uploads are
    fully anonymous — it's what stands between the public endpoints and
    abuse. Requires uvicorn to be run with --proxy-headers so
    request.client.host reflects the real client, not Railway's edge.

    Fails open: if Redis itself is unreachable or errors, the request is
    allowed through rather than turning a Redis hiccup into a site-wide
    outage. Availability of the product beats perfect rate limiting.
    """

    async def _dependency(request: Request):
        identity = request.client.host if request.client else "unknown"
        redis_key = f"ratelimit:{key_prefix}:{identity}"
        try:
            redis = get_redis()
            current = await redis.incr(redis_key)
            if current == 1:
                await redis.expire(redis_key, window_seconds)
        except RedisError:
            logger.warning("Rate limiter: Redis unavailable, failing open for %s", redis_key)
            return

        if current > count:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down and try again shortly.",
            )

    return _dependency
