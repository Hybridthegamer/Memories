import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import engine
from app.files.routes import router as files_router
from app.redis_client import get_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="Storage Platform API")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Baseline hardening headers on every response. Doesn't replace proper
    input validation, but closes off cheap browser-side abuse (MIME
    sniffing, clickjacking, referrer leakage) for free."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejects requests whose declared Content-Length exceeds the configured
    cap before any route handler (or Pydantic) touches the body. Every
    endpoint here is small JSON — actual file uploads go straight to B2 via
    presigned URLs and never pass through this server — so there's no
    legitimate request anywhere near this size. This checks the
    (client-supplied) Content-Length header rather than streamed bytes, so
    it isn't airtight against a chunked-encoding client that omits the
    header, but it stops the overwhelmingly common case cheaply and for
    free, before any memory is spent buffering the body.
    """

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                too_big = int(content_length) > settings.MAX_REQUEST_BODY_BYTES
            except ValueError:
                too_big = False
            if too_big:
                return JSONResponse(status_code=413, content={"detail": "Request body too large"})
        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(BodySizeLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Catch-all so an unexpected error returns a clean 500 instead of crashing
    # the worker process or leaking a traceback to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/healthz")
async def healthz():
    # Actually exercises the DB and Redis rather than just returning "ok" —
    # under multi-replica deployment, an orchestrator uses this to decide
    # whether to route traffic to (or restart) an instance, so it needs to
    # reflect real dependency health, not just "the process is alive".
    checks = {"db": False, "redis": False}

    try:
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=2)
        checks["db"] = True
    except Exception:
        logger.warning("healthz: database check failed", exc_info=True)

    try:
        redis = get_redis()
        await asyncio.wait_for(redis.ping(), timeout=2)
        checks["redis"] = True
    except Exception:
        logger.warning("healthz: redis check failed", exc_info=True)

    healthy = all(checks.values())
    return JSONResponse(status_code=200 if healthy else 503, content={"status": "ok" if healthy else "degraded", **checks})


app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
