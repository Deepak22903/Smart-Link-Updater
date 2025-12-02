# Data Persistence Audit - SmartLink Updater

## Executive Summary
All critical application data is now persisted in MongoDB Atlas and will survive container restarts. The only ephemeral data is temporary files and cache.

## MongoDB Collections (✅ PERSISTENT)

### 1. **posts** - Post Configuration
- **What**: WordPress post configurations with source URLs, extractors, timezones
- **Key Fields**: `post_id`, `source_urls`, `timezone`, `extractor`, `days_to_keep`, `wp_site`, `content_slug`, `site_post_ids`
- **Indexes**: Unique on `post_id`, unique sparse on `content_slug`
- **API**: `/api/posts/*` endpoints
- **Status**: ✅ **Fully persistent in MongoDB**

### 2. **fingerprints** - Link Deduplication
- **What**: Fingerprints of previously processed links to prevent duplicates
- **Key Fields**: `post_id`, `date_iso`, `site_key`, `fingerprints[]`, `updated_at`
- **Format**: `{url}|||{date_iso}` per fingerprint
- **Indexes**: Unique compound on `(post_id, date_iso, site_key)`
- **Status**: ✅ **Fully persistent in MongoDB**

### 3. **wp_sites** - WordPress Sites Configuration
- **What**: WordPress site credentials and configuration
- **Key Fields**: `site_key`, `base_url`, `username`, `app_password`, `display_name`, `created_at`, `updated_at`
- **API**: `/api/sites/*` endpoints
- **Status**: ✅ **Fully persistent in MongoDB** (migrated Dec 2025)

### 4. **monitoring** - HTML Change Detection
- **What**: Fingerprints of source page HTML for structure change detection
- **Key Fields**: `url`, `html_fingerprint`, `last_checked`, `change_count`
- **Purpose**: Alerts when extractor may need updates due to site changes
- **Status**: ✅ **Fully persistent in MongoDB**

### 5. **alerts** - System Alerts
- **What**: Triggered alerts for extraction failures, HTML changes, errors
- **Key Fields**: `alert_type`, `url`, `post_id`, `timestamp`, `message`, `resolved`
- **Status**: ✅ **Fully persistent in MongoDB**

### 6. **batch_requests** - Batch Update Tracking
- **What**: State of batch update operations from WordPress dashboard
- **Key Fields**: `request_id`, `status`, `post_ids`, `site_keys`, `logs[]`, `created_at`, `updated_at`
- **Purpose**: Real-time progress tracking for UI
- **Status**: ✅ **Fully persistent in MongoDB**

### 7. **update_history** - Audit Trail
- **What**: Historical record of all link updates
- **Key Fields**: `post_id`, `date_iso`, `site_key`, `links_added`, `links_updated`, `timestamp`
- **Purpose**: Analytics and debugging
- **Status**: ✅ **Fully persistent in MongoDB**

### 8. **settings** - Application Settings
- **What**: Application-wide settings including cron/scheduled update configuration
- **Key Fields**: `setting_key`, `enabled`, `schedule`, `target_sites`, `updated_at`
- **Collections**: `cron_config` for scheduled updates
- **API**: `/api/cron/settings` endpoints
- **Status**: ✅ **Fully persistent in MongoDB** (migrated Dec 2025)
- **Fallback**: WordPress options table (`wp_options`) as secondary storage

## Ephemeral Data (⚠️ CONTAINER RESTART = LOST)

### 1. **Temp Site Config File** - LEGACY FALLBACK
- **Path**: `/tmp/wp_sites_config.json`
- **Purpose**: Legacy file storage for sites (MongoDB takes priority now)
- **Impact**: ⚠️ **Low** - Only used if MongoDB is unavailable
- **Action**: None needed - MongoDB is primary

### 2. **Application Logs**
- **Path**: Container stdout/stderr
- **Destination**: Cloud Run logs (persistent via Google Cloud Logging)
- **Impact**: ✅ **None** - Logs sent to Cloud Logging in real-time
- **Action**: None needed

### 3. **Python Cache & Temp Files**
- **Examples**: `__pycache__/`, `/tmp/*.html` scraped pages
- **Impact**: ✅ **None** - Automatically regenerated
- **Action**: None needed

### 4. **In-Memory State**
- **What**: FastAPI app state, active HTTP connections, background tasks
- **Impact**: ✅ **None** - Stateless application design
- **Action**: None needed

## Legacy Files (📁 NOT USED)

### backend/data/ Directory
These JSON files are **legacy backups only** and are NOT used by the application:

- ❌ `posts.json` - Replaced by MongoDB `posts` collection
- ❌ `fingerprints.json` - Replaced by MongoDB `fingerprints` collection
- ❌ `monitoring.json` - Replaced by MongoDB `monitoring` collection
- ❌ `alerts.json` - Replaced by MongoDB `alerts` collection

**Evidence**: 
- `storage.py` module exists but is only imported by unused CLI tools (`tasks.py`, `configure_posts.py`)
- Main application (`main.py`) uses `mongo_storage` exclusively
- These files can be deleted without affecting production

### Legacy Code Files
- `backend/app/storage.py` - Old file-based storage module (not imported by main.py)
- `backend/app/tasks.py` - Celery task (not used in Cloud Run deployment)
- `backend/app/configure_posts.py` - CLI tool (replaced by API endpoints)

## Environment Variables (✅ PERSISTENT VIA DEPLOYMENT)

Stored in Cloud Run service configuration (survives restarts):

```bash
MONGODB_URI=mongodb+srv://...
MONGODB_DATABASE=SmartLinkUpdater
WP_BASE_URL=https://... (fallback if no MongoDB)
WP_USERNAME=... (fallback)
WP_APP_PASSWORD=... (fallback)
GEMINI_API_KEY=...
EMAIL_SMTP_HOST=...
EMAIL_SMTP_PORT=...
EMAIL_FROM=...
EMAIL_PASSWORD=...
ALERT_EMAILS=...
```

## Data Loading Priority (How Data is Read)

### WordPress Sites
1. **MongoDB** (`wp_sites` collection) ← PRIMARY
2. `/tmp/wp_sites_config.json` ← Fallback
3. `WP_SITES` environment variable ← Legacy

### Post Configurations
1. **MongoDB** (`posts` collection) ← ONLY SOURCE
2. No fallback

### Link Fingerprints
1. **MongoDB** (`fingerprints` collection) ← ONLY SOURCE
2. No fallback

## Production Readiness Checklist

### ✅ Data Persistence
- [x] Posts configuration persistent
- [x] Link fingerprints persistent
- [x] WordPress sites persistent
- [x] Batch request state persistent
- [x] Monitoring data persistent
- [x] Alerts persistent
- [x] Update history persistent

### ✅ Backup Strategy
- [x] MongoDB Atlas automated backups (point-in-time recovery)
- [x] Multi-region replication via Atlas
- [x] Connection pooling for reliability
- [x] Retry logic on failed connections

### ✅ Stateless Application
- [x] No local file dependencies for core functionality
- [x] No in-memory shared state between requests
- [x] Horizontal scaling ready (multiple containers can run)

## Migration Recommendations

### 1. Clean Up Legacy Files (Optional)
```bash
# These files are safe to delete after confirming MongoDB is working
rm backend/data/posts.json
rm backend/data/fingerprints.json
rm backend/data/monitoring.json
rm backend/data/alerts.json

# Archive legacy code (not imported by main app)
mkdir backend/app/legacy/
mv backend/app/storage.py backend/app/legacy/
mv backend/app/tasks.py backend/app/legacy/
mv backend/app/configure_posts.py backend/app/legacy/
```

### 2. Environment Variable Simplification
After all sites are in MongoDB, you can remove from `deploy.sh`:
```bash
# These become optional fallbacks
WP_BASE_URL
WP_USERNAME
WP_APP_PASSWORD
WP_SITES
```

### 3. Monitoring Setup
Add MongoDB connection health check:
```python
@app.get("/health")
async def health_check():
    try:
        mongo_storage._get_storage().db.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "unhealthy", "database": "disconnected"}
```

## Testing Data Persistence

### Test Container Restart Behavior
```bash
# 1. Add a test site via API
curl -X POST https://your-api.run.app/api/sites/add \
  -H 'Content-Type: application/json' \
  -d '{"site_key": "test", "base_url": "https://test.com", ...}'

# 2. Force container restart
gcloud run services update smartlink-api --region us-central1

# 3. Verify site still exists
curl https://your-api.run.app/api/sites/list
# Should show "test" site

# 4. Check logs for MongoDB load message
gcloud run services logs read smartlink-api --region us-central1 | grep SITES
# Should see: "[SITES] Loaded X sites from MongoDB"
```

### Test MongoDB Connectivity
```bash
# From local dev environment
cd backend
python -c "
from app import mongo_storage
sites = mongo_storage.get_all_wp_sites()
print(f'Found {len(sites)} sites in MongoDB')
posts = mongo_storage.list_configured_posts()
print(f'Found {len(posts)} posts in MongoDB')
"
```

## Conclusion

✅ **All critical data is persistent in MongoDB Atlas**

The application is fully stateless and container-restart-safe. The only data that resets on restart is:
- Python bytecode cache (auto-regenerated)
- Temporary scraped HTML (re-downloaded as needed)
- In-flight HTTP connections (gracefully closed)

**No user configuration or link data is lost on container restarts.**
