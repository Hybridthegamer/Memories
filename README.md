# Memories

A web platform to upload photos/videos and view/download them forever. React frontend, FastAPI backend, Postgres for metadata, and Backblaze B2 (S3-compatible) for object storage.

The backend never proxies file bytes — the browser uploads and downloads directly to/from object storage using short-lived presigned URLs. The backend only handles auth, metadata, and background thumbnail/poster-frame generation.

## Architecture

```
React (Vercel/Netlify) → FastAPI (Railway) → Postgres (metadata) + RQ/Redis (jobs)
        ↓ presigned PUT/GET URLs                        ↓
        └──────────────► Backblaze B2 (private bucket) ◄┘
```

## Stack

- **Backend:** FastAPI, SQLAlchemy (async) + asyncpg, Alembic, RQ + Redis, boto3, Pillow, ffmpeg
- **Frontend:** React + Vite + TypeScript, TanStack Query, Tailwind CSS, axios
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

## Deployment

1. Backend → Railway: deploy `backend/` as a web service (`uvicorn`) and a worker service (`python worker.py`), pointed at Postgres + Redis.
2. Frontend → Vercel/Netlify: deploy `frontend/`, set `VITE_API_BASE_URL` to the backend's public URL.
3. Update `CORS_ALLOWED_ORIGINS` and the B2 bucket CORS policy with the real frontend domain.
4. Set real, random `SECRET_KEY` and B2 credentials as environment variables — never commit `.env`.
