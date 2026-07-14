import redis
from rq import Queue

from app.config import settings

_redis_conn = None
_queue = None


def get_queue() -> Queue:
    global _redis_conn, _queue
    if _queue is None:
        _redis_conn = redis.from_url(settings.REDIS_URL)
        _queue = Queue("file-processing", connection=_redis_conn)
    return _queue
