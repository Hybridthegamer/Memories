FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Overridden by Railway's worker service to run `python worker.py` instead.
#
# --proxy-headers --forwarded-allow-ips='*': trust X-Forwarded-For from the
# immediate upstream (Railway's own edge, the only thing that can reach this
# container directly). Without this, request.client.host is Railway's
# internal proxy IP for every single request — which silently makes all
# per-IP rate limiting a no-op, since every client collapses into one bucket.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'"]
