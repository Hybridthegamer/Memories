import logging

import redis
from rq import Queue, Worker

from app.config import settings

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    conn = redis.from_url(settings.REDIS_URL)
    queue = Queue("file-processing", connection=conn)
    worker = Worker([queue], connection=conn)
    worker.work(with_scheduler=False)
