from fastapi import Depends, HTTPException, Request, status

from app.redis_client import get_redis


def rate_limit_by_ip(key_prefix: str, count: int, window_seconds: int):
    """Fixed-window rate limiter dependency, keyed by client IP.

    Uses Redis INCR + EXPIRE so the check is a couple of cheap round trips
    and stays correct under concurrent requests (INCR is atomic in Redis).
    Intended for unauthenticated endpoints (register/login) to blunt
    brute-force / credential-stuffing attempts.
    """

    async def _dependency(request: Request):
        identity = request.client.host if request.client else "unknown"
        await _check(f"{key_prefix}:{identity}", count, window_seconds)

    return _dependency


def rate_limit_by_user(key_prefix: str, count: int, window_seconds: int):
    """Fixed-window rate limiter dependency, keyed by authenticated user id."""
    from app.deps import get_current_user

    async def _dependency(user=Depends(get_current_user)):
        await _check(f"{key_prefix}:{user.id}", count, window_seconds)
        return user

    return _dependency


async def _check(redis_key_suffix: str, count: int, window_seconds: int) -> None:
    redis = get_redis()
    redis_key = f"ratelimit:{redis_key_suffix}"
    current = await redis.incr(redis_key)
    if current == 1:
        await redis.expire(redis_key, window_seconds)
    if current > count:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down and try again shortly.",
        )
