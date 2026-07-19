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
- `UPLOAD_RATE_LIMIT_COUNT` / `UPLOAD_RATE_LIMIT_WINDOW_SECONDS` are the main abuse guard on a platform with no accounts — they rate-limit upload endpoints per IP. `READ_RATE_LIMIT_*`, `DOWNLOAD_RATE_LIMIT_*`, and `DELETE_RATE_LIMIT_*` do the same for browsing, downloading, and deleting.
- `GLOBAL_STORAGE_QUOTA_BYTES` caps total storage across everyone, not per user, since there's no concept of a user. `PENDING_UPLOAD_STALE_SECONDS` bounds how long an unfinished upload can occupy that quota before it's swept away as abandoned.
- `DELETE_WINDOW_DAYS` controls how long an upload stays deletable by its uploader before it's permanent (default 3).
- `MAX_REQUEST_BODY_BYTES` caps the size of any JSON request body the API will parse.
- `S3_THUMBNAIL_BUCKET_NAME` / `THUMBNAIL_CDN_BASE_URL` (optional) put thumbnails behind a CDN — see "Thumbnail CDN" below.

## Security & abuse-resistance

Because there are no accounts, per-IP identity is all the platform has — every protection below hinges on the deployment target correctly forwarding the real client IP:

- **All public endpoints are rate-limited per IP** (upload, browse/list, download, delete), backed by Redis. If Redis itself is unreachable, the limiter fails open (allows the request) rather than taking the whole site down over a cache hiccup.
- **`X-Forwarded-For` must be trusted correctly.** The Dockerfile runs uvicorn with `--proxy-headers --forwarded-allow-ips='*'`, which is safe *only* because Railway (or whatever platform fronts this) is the sole thing that can reach the container directly — it strips/overwrites any `X-Forwarded-For` the actual client sent before forwarding. Deploying this behind a different topology (e.g. directly exposed to the internet) without re-checking this would silently disable all rate limiting.
- **Storage quota is race-free.** The check-then-reserve for `GLOBAL_STORAGE_QUOTA_BYTES` is wrapped in a Postgres advisory lock (`pg_advisory_xact_lock`) so concurrent uploads can't both slip in under the cap. Abandoned "pending" uploads (URL issued, never used) are excluded from quota accounting after `PENDING_UPLOAD_STALE_SECONDS`, closing off a "spam upload-requests, never upload" quota-exhaustion DoS.
- **Declared upload size is verified, not trusted.** After a client confirms an upload, the backend HEADs the object in B2 and corrects `size_bytes` to the real value — a client under-reporting size to dodge the quota check gains nothing.
- **Failed processing cleans up storage.** If thumbnail/poster generation fails, the original object is deleted from B2 rather than left behind — otherwise repeatedly uploading files designed to fail processing would be a free way to rack up real storage cost outside quota accounting.
- **User-controlled filenames are sanitized** before being embedded in a `Content-Disposition` response header, closing a header-injection vector.
- **B2/boto3 calls have explicit connect/read timeouts and bounded retries**, and the Redis connection pool has socket timeouts — a hung upstream can't tie up a request or worker indefinitely.
- **Security headers** (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) are set on every response, and oversized request bodies are rejected via `MAX_REQUEST_BODY_BYTES` before parsing.
- **`/healthz` checks real dependency health** (a live DB query and a Redis `PING`, both with short timeouts), not just "the process is up" — needed for an orchestrator to make correct routing/restart decisions across multiple replicas.

## Scaling: web + worker replicas

- **API (`uvicorn`)**: the Dockerfile already runs multiple worker processes per container via `--workers ${WEB_CONCURRENCY:-2}`. On Railway, set the service's replica count (or `WEB_CONCURRENCY`) to add more; the app is fully stateless (no in-memory session state — everything shared lives in Postgres/Redis/B2), so it scales horizontally with no code changes.
- **Background worker (RQ)**: also stateless and horizontally scalable — every worker process pulls jobs off the same Redis queue, so running N of them gives N-way parallel thumbnail/poster processing. Locally: `docker compose up --scale worker=4`. On Railway: bump the worker service's replica count the same way as the web service.
- Both scale independently: add web replicas for read/API throughput, worker replicas for upload-processing throughput.

## Thumbnail CDN

Thumbnails are shown to every visitor in the public gallery, so — unlike originals — there's no reason to keep them behind auth-gated presigned URLs; putting them on a CDN lets the edge cache them instead of every viewer re-hitting the origin/B2.

1. Create a second, **public** B2 bucket for thumbnails only (originals stay in the private bucket).
2. Front it with a CDN (e.g. Cloudflare: add the bucket's public endpoint as an origin, proxy a subdomain like `cdn.example.com` through it).
3. Set `S3_THUMBNAIL_BUCKET_NAME` to the new bucket's name and `THUMBNAIL_CDN_BASE_URL` to the CDN's public base URL (e.g. `https://cdn.example.com`).
4. Leave both unset to keep thumbnails in the main private bucket behind presigned URLs (the original default behavior) — no functional change if you don't need CDN-scale thumbnail traffic yet.

## Deployment

1. Backend → Railway: deploy `backend/` as a web service (`uvicorn`) and a worker service (`python worker.py`), pointed at Postgres + Redis. Scale either independently via replica count — see "Scaling" above.
2. Frontend → Vercel/Netlify: deploy `frontend/`, set `VITE_API_BASE_URL` to the backend's public URL.
3. Update `CORS_ALLOWED_ORIGINS` and the B2 bucket CORS policy with the real frontend domain.
4. Set real B2 credentials as environment variables — never commit `.env`.
5. (Optional) Set up a thumbnail CDN — see "Thumbnail CDN" above.
