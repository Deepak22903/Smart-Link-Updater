# SmartLinkUpdater (Option 2: External worker + queue)

A minimal, Dockerized skeleton for updating WordPress posts by scraping target sites, extracting only today's links (Gemini-ready), and updating posts via WP REST. Runs API + Celery worker + Redis locally.

## Architecture (high level)

- API: FastAPI (`/trigger`) enqueues one Celery job per post.
- Worker: Celery worker orchestrates scraping → Gemini parsing (stubbed) → filter/dedupe → WordPress update.
- Queue: Redis (local docker) for broker/result.
- Scraping: `httpx` by default; optional ScraperAPI via env (`SCRAPER_API_URL`, `SCRAPER_API_KEY`).
- LLM: Gemini placeholder in `app/llm.py` (plug your key + SDK and enforce JSON schema).

## Why not Vercel for workers?

Vercel does not run persistent Docker containers. It provides Serverless/Edge/Background Functions with execution time limits and no always-on queue consumers. For a true queue + worker model, use:

- Google Cloud Run (containers), AWS ECS/Fargate, Azure Container Apps
- Fly.io, Railway, Render, or a VPS

MongoDB Atlas is great for storing post/link metadata. Use Redis (e.g., Upstash Redis) for the queue. If you must stay on Vercel, consider Upstash QStash (HTTP push) to invoke Background Functions, but it's less suitable for heavy scraping workers.

## Local quickstart

1. Copy env template and fill WP creds:

```bash
cp .env.example .env
```

2. Build and run:

```bash
docker compose up --build
```

3. Health check:

```bash
curl http://localhost:8000/health
```

4. Enqueue a test job (replace values):

```bash
curl -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 123,
    "source_urls": ["https://news.ycombinator.com/"],
    "timezone": "Asia/Kolkata",
    "today_iso": "2025-10-26"
  }'
```

Note: Gemini call is stubbed; update `app/llm.py` to integrate Google Gemini and return the strict JSON as described in the docs.

## File layout

- `backend/app/main.py` – FastAPI API (`/trigger`)
- `backend/app/queue_app.py` – Celery app and config
- `backend/app/tasks.py` – Celery task orchestrating scrape → extract → update
- `backend/app/scrape.py` – HTML fetch (direct or via ScraperAPI)
- `backend/app/llm.py` – Gemini placeholder: implement schema-constrained parsing
- `backend/app/dedupe.py` – filter-only-today + dedupe by fingerprint
- `backend/app/wp.py` – WordPress REST client (Basic Auth via Application Password)
- `backend/tests/test_dedupe.py` – minimal unit tests for dedupe logic
- `backend/Dockerfile` – shared for API and worker
- `docker-compose.yml` – brings up Redis, API, worker

## Production hosting options

- Containers: Cloud Run, ECS/Fargate, Azure Container Apps, Fly.io, Railway, Render
- Queue/Cache: Redis (Upstash, Redis Cloud). If on GCP, Cloud Tasks is a solid option.
- DB: MongoDB Atlas for persistent storage of link fingerprints, logs, and per-post config.
- Scraping: Apify for JS-heavy sites; ScraperAPI/ZenRows for lightweight pages; Playwright in a container if self-hosting.
- Observability: Sentry, structured logs, per-post run logs persisted in DB.

## Next steps

- Implement Gemini extraction in `app/llm.py` with your prompt + strict JSON schema.
- Persist known fingerprints and last-run state in MongoDB Atlas.
- Enhance `app/wp.py` to write to a custom field or block rather than prefixing content.
- Add per-domain rate limiting and retries/backoff policies.
- Provide a small WordPress plugin button that calls this API.
