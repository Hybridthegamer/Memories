from fastapi import HTTPException, Request, status

from app.redis_client import get_redis


def rate_limit_by_ip(key_prefix: str, count: int, window_seconds: int):
    """Fixed-window rate limiter dependency, keyed by client IP.

    Uses Redis INCR + EXPIRE so the check is a couple of cheap round trips
    and stays correct under concurrent requests (INCR is atomic in Redis).
    This is the only identity signal available now that uploads are fully
    anonymous — it's what stands between the public upload endpoints and
    abuse.
    """

    async def _dependency(request: Request):
        identity = request.client.host if request.client else "unknown"
        redis = get_redis()
        redis_key = f"ratelimit:{key_prefix}:{identity}"
        current = await redis.incr(redis_key)
        if current == 1:
            await redis.expire(redis_key, window_seconds)
        if current > count:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down and try again shortly.",
            )

    return _dependency
