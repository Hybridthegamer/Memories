import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth.routes import router as auth_router
from app.config import settings
from app.files.routes import router as files_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

app = FastAPI(title="Storage Platform API")

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
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
