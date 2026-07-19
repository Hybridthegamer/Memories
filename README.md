# Memories

A public wall for photos and videos — no accounts. Anyone can drop a photo or video onto the wall, everyone can see and download everything on it. An upload is deletable only by whoever added it (proven by a token their browser holds), and only within 3 days; after that it's permanent for good. React frontend, FastAPI backend, Postgres for metadata, and Backblaze B2 (S3-compatible) for object storage.

The backend never proxies file bytes — the browser uploads and downloads directly to/from object storage using short-lived presigned URLs. The backend only handles metadata, abuse-rate-limiting, and background thumbnail/poster-frame generation.

## How "no accounts, but you can still delete your own upload" works

There's no login anywhere. At upload time the server generates a random delete token, returns it to the browser exactly once, and only ever stores its hash. The browser keeps that token in `localStorage`. Deleting a file requires presenting the matching token — and the server independently checks the file is still within its 3-day window, regardless of what the client claims. Clear your browser data or switch devices and you lose delete rights on your own past uploads; that's the accepted tradeoff for a platform with no sign-up.

## Architecture

```
React (Vercel/Netlify) → FastAPI (Railway) → Postgres (metadata) + RQ/Redis (jobs)
        ↓ presigned PUT/GET URLs                        ↓
        └──────────────► Backblaze B2 (private bucket) ◄┘
```

## Stack

- **Backend:** FastAPI, SQLAlchemy (async) + asyncpg, Alembic, RQ + Redis, boto3, Pillow, ffmpeg
- **Frontend:** React + Vite + TypeScript, TanStack Query, Tailwind CSS + Framer Motion, axios
- **Infra:** Postgres, Redis, Backblaze B2, Railway (backend + worker), Vercel/Netlify (frontend)

## Local development

Requires Docker.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# fill in backend/.env with your Backblaze B2 credentials + bucket

docker compose up --build
```

- Backend API: http://localhost:8000/api/v1 (docs at `/docs`)
- Then, separately, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173

## Configuration

All config is via environment variables — see `backend/.env.example` and `frontend/.env.example`. Notably:

- `CORS_ALLOWED_ORIGINS` on the backend must include every frontend origin.
- The B2 **bucket's own CORS policy** (set in the B2 console, not in app code) must separately allow `PUT`/`GET` from those same origins — this is required in addition to FastAPI's CORS middleware, since the browser talks to B2 directly.
- The bucket stays private; all access is via presigned URLs.
- `UPLOAD_RATE_LIMIT_COUNT` / `UPLOAD_RATE_LIMIT_WINDOW_SECONDS` are the main abuse guard on a platform with no accounts — they rate-limit upload endpoints per IP.
- `GLOBAL_STORAGE_QUOTA_BYTES` caps total storage across everyone, not per user, since there's no concept of a user.
- `DELETE_WINDOW_DAYS` controls how long an upload stays deletable by its uploader before it's permanent (default 3).

## Deployment

1. Backend → Railway: deploy `backend/` as a web service (`uvicorn`) and a worker service (`python worker.py`), pointed at Postgres + Redis.
2. Frontend → Vercel/Netlify: deploy `frontend/`, set `VITE_API_BASE_URL` to the backend's public URL.
3. Update `CORS_ALLOWED_ORIGINS` and the B2 bucket CORS policy with the real frontend domain.
4. Set real B2 credentials as environment variables — never commit `.env`.
