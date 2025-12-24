# SmartLink Updater - AI Coding Agent Guide

## System Overview
WordPress link automation system that scrapes reward/gaming sites, extracts links using AI/custom extractors, deduplicates by fingerprint, and updates WordPress posts via REST API. Deployed on Google Cloud Run with MongoDB Atlas storage.

## Architecture Components

### 1. FastAPI Backend (`backend/app/`)
- **main.py**: Core API with endpoints for `/trigger`, `/api/batch-update`, `/api/posts/*`
- **Sync vs Async modes**: `?sync=true` for WordPress plugin (immediate response), default for Cloud Scheduler (background)
- **Multi-site support**: Updates multiple WordPress installations from single API call using `WP_SITES` env var

### 2. Modular Extractor System (`backend/app/extractors/`)
**Critical pattern**: Plugin-based architecture for scalability
- Each extractor inherits from `BaseExtractor` with `can_handle()` and `extract()` methods
- Auto-registered via decorator: `@register_extractor("site_name")`
- **Auto-detection**: System uses `get_extractor_for_url()` to automatically select the right extractor based on domain
- **Multi-day fingerprints**: Extractors can override `check_previous_days()` to check previous days' fingerprints (e.g., WSOP checks yesterday to avoid re-adding old links)
- **Example**: `simplegameguide.py` - looks for h4 date headers, extracts links from following section
- **Fallback**: `default.py` uses Gemini AI when no specific extractor matches
- **Add new sites**: Copy extractor template, modify 20 lines - NO changes to `main.py` needed!

### 3. Data Storage Layers
- **MongoDB** (`mongo_storage.py`): Primary storage for configs, fingerprints, alerts, batch state
- **JSON files** (`backend/data/`): Legacy fallback for `posts.json`, `fingerprints.json`
- **Fingerprinting** (`dedupe.py`): `{url}___{date_iso}` format prevents duplicate link insertions
- **Multi-day deduplication**: `get_fingerprints_with_lookback()` automatically loads fingerprints for today and N previous days based on extractor configuration

### 4. WordPress Integration
- **Authentication**: Basic Auth with Application Passwords (not user passwords!)
- **Block insertion**: Uses Gutenberg block parser to insert after specific anchor comment: `<!-- SmartLink Updater: Daily Links -->`
- **Multi-site resolution**: `resolve_post_id_for_site()` maps one content slug to different post IDs per site via `site_post_ids` dict

## Critical Developer Workflows

### Deploy to Google Cloud Run
```bash
./deploy.sh  # Builds via Cloud Build, deploys with env vars from script
```
**Note**: Never commit credentials! Use `env-config.yaml` for multi-site setups (not in repo)

### Add New Post (Existing Site)
Edit `backend/data/posts.json` only:
```json
{
  "1234": {
    "post_id": 1234,
    "source_urls": ["https://simplegameguide.com/new-page/"],
    "timezone": "Asia/Kolkata",
    "extractor": "simplegameguide"  // Reuses existing extractor
  }
}
```

### Create Custom Extractor (New Site)
1. Copy `backend/app/extractors/simplegameguide.py` to `backend/app/extractors/newsite.py`
2. Modify `can_handle()` to match domain, adjust extraction logic in `extract()`
3. If extractor includes previous days' links, override `check_previous_days()` to return lookback days (e.g., return 1 for yesterday)
4. Update `posts.json` with source URLs - extractor will be auto-detected by domain!
5. See `EXTRACTOR_GUIDE.md` and `MULTI_DAY_FINGERPRINT_CHECKING.md` for detailed templates

### Test Extractor Locally
```bash
# Run specific test matching extractor name
python -m pytest backend/tests/test_mosttechs_extractor.py -v
```

### Local Development
```bash
# API only (no Celery/Redis)
cd backend
uvicorn app.main:app --reload --port 8000

# Full stack with worker queue
docker compose up --build  # Redis + API + Celery worker
```

## Project-Specific Patterns

### Date Format Handling
- **Storage**: Always ISO format `YYYY-MM-DD` (`published_date_iso`)
- **Display**: Convert in extractors to match site format (e.g., "26 October 2025", "Nov 4, 2025:")
- **Timezone**: Posts have `timezone` field; use `pytz` for today's date calculation

### Link Target Attribute
Function `get_link_target()` in `wp.py` controls `_blank` (new tab) vs `_self` (same tab)
Default: `_blank` for external links. Customize for specific domains (e.g., Telegram links).

### WordPress Block Insertion
**Never replace entire post content!** Look for anchor comment:
```html
<!-- SmartLink Updater: Daily Links -->
<!-- /SmartLink Updater: Daily Links -->
```
Insert new Gutenberg list block between these markers. See `insert_or_replace_links_section()` in `wp.py`.

### Batch Update States (Dashboard)
Uses `batch_manager.py` with MongoDB persistence:
- `QUEUED` → `RUNNING` → `SUCCESS`/`NO_CHANGES`/`FAILED`
- Real-time progress via `/api/batch-status/{request_id}` polling
- Logs streamed to dashboard: `state.add_log("message")`

### Error Handling & Monitoring
- **HTML Change Detection**: `html_monitor.py` fingerprints pages, creates alerts on structural changes
- **Email Alerts**: `notifications.py` sends via SMTP when extraction fails or site structure changes
- **Analytics**: `analytics.py` tracks success rates, performance metrics per post/extractor

## Integration Points

### WordPress Plugin (`wordpress-plugin/smartlink-updater.php`)
- **Server-side AJAX**: Calls API with `?sync=true` to avoid CORS issues
- **Dashboard UI**: Real-time batch updates with progress bars, post-level logs
- **REST API Proxy**: WordPress REST endpoints forward to Cloud Run API

### Google Cloud Services
- **Cloud Run**: Auto-scaling containers (512Mi RAM, 1 CPU, max 10 instances)
- **Secret Manager**: Not used (uses env vars for simplicity)
- **Cloud Build**: Automated Docker builds from GitHub pushes

### MongoDB Atlas
- **Collections**: `posts`, `fingerprints`, `monitoring`, `alerts`, `batch_requests`, `analytics`
- **Indexes**: Unique on `post_id`, `content_slug`; compound on `(post_id, date_iso, site_key)`
- **Connection**: Uses connection pooling, 5s timeout, retry logic

### Gemini AI (Fallback Extractor)
Stub in `llm.py` - requires API key and schema enforcement
When no specific extractor matches, calls Gemini to parse HTML and return JSON with links

## Anti-Patterns to Avoid

1. **Don't hardcode credentials** - Use env vars (checked into `deploy.sh` for demo, but use Secret Manager in prod)
2. **Don't modify `main.py` for new sites** - Use extractor plugins instead
3. **Don't use user passwords for WP** - Only Application Passwords (generated in WP admin)
4. **Don't block on scraping** - Use `BackgroundTasks` for parallel post processing
5. **Don't fingerprint without date** - Format is `{url}|||{date_iso}`, not just URL

## Testing Strategy

### Unit Tests
- `backend/tests/test_dedupe.py` - Fingerprint logic
- `backend/tests/test_mosttechs_extractor.py` - Extractor pattern matching

### Integration Tests
```bash
# Test full pipeline for single post
curl -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{"post_id": 105, "source_urls": ["https://..."], "timezone": "Asia/Kolkata"}'

# Test multi-site batch update
curl -X POST http://localhost:8000/api/batch-update \
  -H 'Content-Type: application/json' \
  -d '{"post_ids": [105, 4163], "target_sites": ["all"]}'
```

### Debugging
- Cloud Run logs: `gcloud run services logs read smartlink-api --region us-central1`
- Local logs: Uvicorn outputs to stdout with structured logging via `logging_conf.py`
- WordPress debug: Check Network tab in browser for AJAX responses

## Key Files Reference

| File | Purpose | When to Modify |
|------|---------|---------------|
| `backend/app/main.py` | API routes | Add new endpoints only |
| `backend/data/posts.json` | Post configs | Every new post |
| `backend/app/extractors/*.py` | Site parsers | New site structure |
| `backend/app/wp.py` | WordPress client | Auth, block insertion logic |
| `backend/app/dedupe.py` | Deduplication | Change fingerprint format |
| `deploy.sh` | Deployment script | Update env vars, region |
| `wordpress-plugin/smartlink-updater.php` | WP dashboard | UI changes |

## Documentation Files

- `EXTRACTOR_GUIDE.md` - Step-by-step extractor creation
- `ARCHITECTURE.md` - System design decisions
- `MULTI_SITE_SETUP.md` - Configure multiple WordPress sites
- `DEPLOYMENT_GUIDE.md` - Production deployment checklist
- `FEATURE_DOCUMENTATION.md` - Feature flags and toggles
