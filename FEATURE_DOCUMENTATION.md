# SmartLink Updater - Feature Documentation

**Version:** 2.0.0  
**Last Updated:** November 9, 2025  
**Status:** Production-Ready with Multi-Site Support

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Implemented Features](#implemented-features)
3. [Architecture](#architecture)
4. [API Endpoints](#api-endpoints)
5. [WordPress Plugin Features](#wordpress-plugin-features)
6. [Extractors](#extractors)
7. [Database Schema](#database-schema)
8. [Planned Features](#planned-features)
9. [Configuration Guide](#configuration-guide)

---

## System Overview

SmartLink Updater is an automated link management system that:
- Scrapes source websites for daily link updates
- Extracts relevant links using custom extractors or AI (Gemini)
- Deduplicates links per-site using SHA-256 fingerprinting
- Updates WordPress posts via REST API
- Monitors source health and sends alerts
- Supports multiple WordPress sites with site-specific post ID mapping

**Tech Stack:**
- Backend: Python 3.13, FastAPI, MongoDB Atlas
- Frontend: WordPress Plugin (PHP, jQuery)
- Deployment: Google Cloud Run
- Database: MongoDB Atlas
- AI: Google Gemini API (for fallback extraction)

---

## Implemented Features

### ✅ Core Functionality

#### 1. **Multi-Site Post Management** (v2.0.0)
- **Status:** ✅ Fully Implemented
- **Description:** Manage the same content across multiple WordPress installations
- **Key Components:**
  - `content_slug`: Universal identifier for content (e.g., "coin-master-free-spins")
  - `site_post_ids`: Maps site keys to site-specific post IDs
  - Site-specific fingerprint tracking for independent deduplication
  - `resolve_post_id_for_site()`: Automatic post ID resolution
- **Files:**
  - `backend/app/main.py`: Multi-site update logic
  - `backend/app/mongo_storage.py`: Site-specific fingerprint storage
  - `wordpress-plugin/smartlink-updater.php`: Multi-site UI

**Example Config:**
```json
{
  "post_id": 206,
  "content_slug": "coin-master-free-spins",
  "site_post_ids": {
    "this": 206,
    "WSOP": 456,
    "minecraft": 789
  },
  "source_urls": ["https://mosttechs.com/coin-master-free-spins/"]
}
```

#### 2. **Custom Extractors** 
- **Status:** ✅ Fully Implemented
- **Description:** Site-specific HTML parsers for reliable link extraction
- **Implemented Extractors:**
  1. **MostTechsExtractor** - Extracts links from mosttechs.com
     - Date-boundary detection (stops at yesterday's date)
     - Handles today's date section
     - Returns: title, URL
  2. **SimpleGameGuideExtractor** - Extracts from simplegameguide.com
     - Custom HTML structure parsing
  3. **TechyHigherExtractor** - Extracts from techyhigher.com
  4. **CrazyAshwinExtractor** - Extracts from crazyashwin.com
  5. **DefaultExtractor** (Gemini-based) - AI fallback for any site
- **Features:**
  - Per-source URL extractor mapping (`extractor_map`)
  - Auto-detection from base URL
  - Fallback to Gemini for unmapped URLs
- **Files:**
  - `backend/app/extractors/` (directory)
  - `backend/app/extractors/__init__.py`: Extractor registry
  - Individual extractor files: `mosttechs.py`, `simplegameguide.py`, etc.

#### 3. **Link Deduplication**
- **Status:** ✅ Fully Implemented
- **Description:** SHA-256 fingerprinting prevents duplicate links
- **Features:**
  - Site-specific deduplication (same link can exist on different sites)
  - Per-date tracking (links reset daily)
  - Fingerprint stored as: `(post_id, date_iso, site_key, fingerprint)`
  - MongoDB unique index: `(post_id, date_iso, site_key)`
- **Files:**
  - `backend/app/dedupe.py`: Fingerprint calculation
  - `backend/app/mongo_storage.py`: Fingerprint storage and retrieval

#### 4. **Batch Updates**
- **Status:** ✅ Fully Implemented
- **Description:** Update multiple posts concurrently with progress tracking
- **Features:**
  - Concurrent processing (10 posts at a time)
  - Real-time progress tracking per post
  - Live log streaming
  - Target selection: single site, all sites, or specific site
  - Status tracking: queued, running, success, failed, no_changes
- **Endpoints:**
  - `POST /api/batch-update`
  - `GET /api/batch-status/{request_id}`
  - `GET /api/batch-logs/{request_id}/{post_id}`
- **Files:**
  - `backend/app/main.py`: Batch orchestration
  - `backend/app/batch_manager.py`: State management
  - `backend/app/mongo_models.py`: BatchUpdateRequest, PostUpdateState models

#### 5. **WordPress Integration**
- **Status:** ✅ Fully Implemented
- **Description:** Direct WordPress REST API integration
- **Features:**
  - Application Password authentication
  - Automatic `<h2>Links</h2>` section management
  - Old section pruning (keeps only today's links)
  - Multi-site support with per-site credentials
  - Site configuration via environment variables
- **Files:**
  - `backend/app/wp.py`: WordPress API client
  - `backend/app/config.py`: Site configuration loader

#### 6. **Source Health Monitoring**
- **Status:** ✅ Fully Implemented
- **Description:** Track extraction success rates and HTML changes
- **Features:**
  - Per-source URL tracking
  - Consecutive failure detection
  - HTML fingerprinting (detect structural changes)
  - Confidence scoring
  - Health status: healthy, warning, failing, critical
  - Alert generation on failures
- **Endpoints:**
  - `GET /health/extractors`
  - `GET /health/extractors/{source_url}`
- **Files:**
  - `backend/app/html_monitor.py`: Health tracking
  - `backend/app/mongo_models.py`: SourceMonitoring model

#### 7. **Alert System**
- **Status:** ✅ Fully Implemented
- **Description:** Automated notifications for failures and issues
- **Features:**
  - Email alerts (SMTP)
  - Webhook alerts (Slack, Discord, custom endpoints)
  - Alert types: extraction_failure, html_change, consecutive_failures
  - Severity levels: info, warning, error, critical
  - Notification tracking (sent/unsent)
- **Endpoints:**
  - `GET /alerts`
  - `GET /alerts/unnotified`
  - `POST /alerts/send`
- **Files:**
  - `backend/app/notifications.py`: Alert delivery
  - `backend/app/mongo_models.py`: Alert model

#### 8. **WordPress Dashboard Plugin**
- **Status:** ✅ Fully Implemented
- **Description:** Full-featured admin interface
- **Features:**
  - Real-time batch update monitoring
  - Post configuration management (add, edit, delete)
  - Live log viewing
  - Search and filter posts
  - Health status display
  - Scheduled updates (WP-Cron)
  - Multi-site post ID management UI
  - Three-dot menu with actions: View Logs, Edit, Delete
- **File:** `wordpress-plugin/smartlink-updater.php`

#### 9. **Scheduled Updates (WP-Cron)**
- **Status:** ✅ Fully Implemented
- **Description:** Automatic periodic updates via WordPress Cron
- **Features:**
  - Configurable schedules: 5 min, 15 min, 30 min, hourly, twice daily, daily
  - Enable/disable toggle
  - Execution history tracking
  - Cron status monitoring
  - Updates ALL configured posts on each run
- **Implementation:** WordPress plugin with REST API triggers

#### 10. **Post Configuration API**
- **Status:** ✅ Fully Implemented
- **Description:** CRUD operations for post configurations
- **Endpoints:**
  - `POST /config/post` - Add new post
  - `GET /config/post/{post_id}` - Get config
  - `PUT /config/post/{post_id}` - Update config
  - `DELETE /config/post/{post_id}` - Delete config
  - `GET /config/posts` - List all configs
- **Features:**
  - Backward-compatible migrations
  - Smart config resolution (content_slug → post_id fallback)
- **Files:**
  - `backend/app/main.py`: API endpoints
  - `backend/app/mongo_storage.py`: Storage layer

#### 14. **Analytics Dashboard**
- **Status:** ✅ Fully Implemented
- **Description:** Comprehensive analytics with charts and performance metrics
- **Features:**
  - Dashboard summary with key metrics (updates, success rate, links added)
  - Timeline charts (daily/weekly/hourly updates)
  - Success rate visualization (doughnut chart)
  - Links added trend (bar chart)
  - Hourly activity patterns (24-hour distribution)
  - Post performance table (top performing posts)
  - Source performance table (extraction success by source)
  - Extractor performance comparison
  - Multi-site performance breakdown
  - Configurable time periods (7, 30, 60, 90 days)
  - Real-time data refresh
- **Charts Library:** Chart.js 4.4.0
- **Endpoints:**
  - `GET /api/analytics/dashboard` - Summary metrics
  - `GET /api/analytics/timeline` - Timeline data
  - `GET /api/analytics/posts` - Post performance
  - `GET /api/analytics/sources` - Source performance
  - `GET /api/analytics/extractors` - Extractor comparison
  - `GET /api/analytics/sites` - Multi-site metrics
  - `GET /api/analytics/hourly-pattern` - Activity by hour
  - `GET /api/analytics/links-trend` - Daily links trend
- **Files:**
  - `backend/app/analytics.py`: Analytics engine
  - `backend/app/main.py`: API endpoints
  - `wordpress-plugin/smartlink-updater.php`: Dashboard UI

---

### ✅ Data Persistence

#### 11. **MongoDB Storage**
- **Status:** ✅ Fully Implemented
- **Description:** Complete migration from JSON files to MongoDB Atlas
- **Collections:**
  - `posts`: Post configurations
  - `fingerprints`: Link deduplication tracking
  - `source_monitoring`: Health metrics
  - `alerts`: Alert history
  - `batch_requests`: Batch update tracking
  - `link_history`: Update history
- **Features:**
  - Connection pooling
  - Index management
  - Migration scripts
- **Files:**
  - `backend/app/mongo_storage.py`: Storage layer
  - `backend/app/mongo_models.py`: Pydantic models
  - `backend/migrate_index.py`: Index migration script
  - `backend/migrate_fingerprints.py`: Fingerprint migration script

---

### ✅ Deployment & Infrastructure

#### 12. **Google Cloud Run Deployment**
- **Status:** ✅ Production-Deployed
- **URL:** `https://smartlink-api-601738079869.us-central1.run.app`
- **Features:**
  - Automatic scaling
  - HTTPS enabled
  - Environment variables for secrets
  - Cloud Build integration
- **Files:**
  - `Dockerfile`
  - `deploy.sh`
  - `.gcloudignore`

#### 13. **Environment Configuration**
- **Status:** ✅ Fully Implemented
- **Features:**
  - Multi-site WordPress credentials
  - MongoDB Atlas connection
  - Gemini API key
  - SMTP email settings
  - Webhook URLs
- **File:** `.env` (with `.env.example` template)

---

## Architecture

### System Flow

```
WordPress Admin → REST API → FastAPI Backend → MongoDB Atlas
                              ↓
                        Extractors (Custom/Gemini)
                              ↓
                        Deduplication Engine
                              ↓
                        WordPress API Update
                              ↓
                        Fingerprint Storage
```

### Multi-Site Architecture

```
Config: {
  content_slug: "coin-master-free-spins",
  site_post_ids: {
    "this": 206,
    "WSOP": 456
  }
}

Update Request (target="WSOP")
  ↓
resolve_post_id_for_site(config, "WSOP")
  ↓
Returns: 456
  ↓
get_known_fingerprints(456, "2025-11-09", "WSOP")
  ↓
update_post_links_section(456, links, "WSOP")
  ↓
save_new_links(456, "2025-11-09", fingerprints, "WSOP")
```

---

## API Endpoints

### Health & Monitoring
- `GET /health` - API health check
- `GET /health/extractors` - All source health statuses
- `GET /health/extractors/{source_url}` - Specific source health
- `GET /alerts` - Get recent alerts
- `GET /alerts/unnotified` - Get unsent alerts
- `POST /alerts/send` - Send pending alerts

### Post Configuration
- `POST /config/post` - Create post configuration
- `GET /config/post/{post_id}` - Get configuration
- `PUT /config/post/{post_id}` - Update configuration
- `DELETE /config/post/{post_id}` - Delete configuration
- `GET /config/posts` - List all configurations
- `GET /config/sites` - List WordPress sites

### Updates
- `POST /update-post/{post_id}` - Single post update
- `POST /api/batch-update` - Batch update multiple posts
- `GET /api/batch-status/{request_id}` - Batch progress
- `GET /api/batch-logs/{request_id}/{post_id}` - Post logs

### Admin
- `GET /api/posts/list` - List posts with health info
- `GET /api/extractors/list` - List available extractors
- `GET /api/sites/list` - List WordPress sites

---

## WordPress Plugin Features

### Dashboard
1. **Batch Controls**
   - Select all/none
   - Target selection (this site, all sites, specific site)
   - Batch update button
   - Real-time progress tracking

2. **Post Table**
   - Columns: Post ID, Title, Content Slug, Extractor, Status, Progress, Last Updated, Health, Actions
   - Checkboxes for batch selection
   - Action buttons: Update, Three-dot menu (View Logs, Edit, Delete)
   - Search and filter

3. **Configuration Modal**
   - Add/Edit post configurations
   - Source URL management (multiple URLs)
   - Extractor selection per URL
   - Site-specific post ID mapping
   - Content slug management

4. **Logs Modal**
   - Real-time log streaming
   - Filterable by post
   - Auto-refresh
   - Export logs

5. **Cron Management**
   - Enable/disable scheduler
   - Schedule selection
   - Execution history
   - Next run time display

---

## Extractors

### Available Extractors

| Extractor | Site | Status | Date Detection | Special Features |
|-----------|------|--------|----------------|------------------|
| **MostTechsExtractor** | mosttechs.com | ✅ Active | Yes (yesterday boundary) | Handles multiple date formats |
| **SimpleGameGuideExtractor** | simplegameguide.com | ✅ Active | No | Custom HTML structure |
| **TechyHigherExtractor** | techyhigher.com | ✅ Active | No | - |
| **CrazyAshwinExtractor** | crazyashwin.com | ✅ Active | No | - |
| **DefaultExtractor** | Any site | ✅ Active | Yes | Gemini AI-powered |

### Extractor Selection Logic

1. Check `extractor_map` for URL-specific mapping
2. If found, use mapped extractor
3. If not found, use DefaultExtractor (Gemini)

**Example extractor_map:**
```json
{
  "https://mosttechs.com/coin-master/": "mosttechs",
  "https://simplegameguide.com/daily-links/": "simplegameguide"
}
```

---

## Database Schema

### Collections

#### 1. **posts**
```json
{
  "post_id": 206,
  "content_slug": "coin-master-free-spins",
  "site_post_ids": {
    "this": 206,
    "WSOP": 456
  },
  "source_urls": ["https://example.com"],
  "timezone": "Asia/Kolkata",
  "extractor_map": {
    "https://example.com": "mosttechs"
  },
  "wp_site": {"base_url": "...", "username": "...", "app_password": "..."},
  "last_updated": "2025-11-09T10:00:00",
  "created_at": "2025-10-26T09:00:00"
}
```

#### 2. **fingerprints**
```json
{
  "post_id": 456,
  "date_iso": "2025-11-09",
  "site_key": "WSOP",
  "fingerprint": "sha256_hash",
  "created_at": "2025-11-09T10:15:00"
}
```

**Unique Index:** `(post_id, date_iso, site_key)`

#### 3. **source_monitoring**
```json
{
  "source_url": "https://example.com",
  "total_extractions": 150,
  "successful_extractions": 145,
  "failed_extractions": 5,
  "consecutive_failures": 0,
  "last_success": "2025-11-09T10:00:00",
  "last_failure": null,
  "confidence_score": 0.97,
  "html_fingerprint": {...}
}
```

#### 4. **alerts**
```json
{
  "source_url": "https://example.com",
  "alert_type": "extraction_failure",
  "severity": "warning",
  "message": "Failed to extract links",
  "details": {...},
  "notification_sent": false,
  "created_at": "2025-11-09T10:00:00"
}
```

#### 5. **batch_requests**
```json
{
  "request_id": "batch_20251109_100000",
  "post_ids": [206, 114, 105],
  "status": "running",
  "initiator": "wp-plugin",
  "target": "WSOP",
  "posts": {
    "206": {
      "status": "success",
      "progress": 100,
      "message": "Added 3 links",
      "logs": ["[10:00:15] Starting...", "..."]
    }
  }
}
```

---

## Planned Features

### 🔄 In Progress

None currently - all major features implemented.

### 📋 Backlog / Future Enhancements

#### 1. **Advanced Scheduling**
- **Priority:** Medium
- **Description:** More flexible scheduling beyond WP-Cron
- **Features:**
  - Per-post custom schedules
  - Time-of-day scheduling
  - Timezone-aware scheduling
  - Retry logic for failed updates

#### 2. **Analytics Dashboard**
- **Priority:** Low
- **Description:** Insights into link update patterns
- **Features:**
  - Update frequency charts
  - Success rate trends
  - Most active sources
  - Performance metrics

#### 3. **Link Quality Scoring**
- **Priority:** Low
- **Description:** Rank links by relevance
- **Features:**
  - ML-based relevance scoring
  - User feedback integration
  - Automatic filtering of low-quality links

#### 4. **Webhook Integrations**
- **Priority:** Low
- **Description:** Trigger external actions on updates
- **Features:**
  - Post-update webhooks
  - Zapier integration
  - Make.com integration
  - Custom webhook payloads

#### 5. **Link Preview Generation**
- **Priority:** Low
- **Description:** Generate preview cards for links
- **Features:**
  - Fetch Open Graph metadata
  - Screenshot generation
  - Thumbnail caching

#### 6. **Multi-Language Support**
- **Priority:** Low
- **Description:** Detect and handle multi-language content
- **Features:**
  - Language detection
  - Per-language extractors
  - Translation integration

#### 7. **A/B Testing**
- **Priority:** Very Low
- **Description:** Test different update strategies
- **Features:**
  - Update strategy variants
  - Performance comparison
  - Automatic optimization

---

## Configuration Guide

### Environment Variables

```bash
# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/SmartLinkUpdater
MONGODB_DB_NAME=SmartLinkUpdater

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# WordPress Sites (Multi-site support)
# Format: SITE_KEY|base_url|username|app_password
WP_SITES=this|https://site1.com|user1|pass1,WSOP|https://site2.com|user2|pass2

# Email Alerts
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your_password
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=admin@yourdomain.com

# Webhook Alerts
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Timezone
TIMEZONE=Asia/Kolkata
```

### WordPress Plugin Configuration

1. Install plugin in WordPress
2. Activate plugin
3. Go to **SmartLink** menu in admin
4. Configure posts:
   - Add post ID
   - Add source URLs
   - Select extractors
   - Add content slug (for multi-site)
   - Map site-specific post IDs

### Adding New WordPress Site

1. Add credentials to `.env`:
   ```
   WP_SITES=existing,newsite|https://newsite.com|username|app_password
   ```

2. Update post configs with `site_post_ids`:
   ```json
   {
     "site_post_ids": {
       "this": 206,
       "newsite": 123
     }
   }
   ```

3. Restart backend (Cloud Run will auto-deploy)

---

## Migration Guide

### From Single-Site to Multi-Site

1. **Run Index Migration:**
   ```bash
   cd backend
   python migrate_index.py
   ```

2. **Run Fingerprint Migration:**
   ```bash
   python migrate_fingerprints.py
   ```
   - Adds `site_key="this"` to existing fingerprints

3. **Update Post Configs:**
   - Add `content_slug` to each post
   - Add `site_post_ids` mapping
   - Use WordPress plugin UI or API

4. **Restart Backend:**
   - Cloud Run auto-deploys on git push
   - Or manually: `./deploy.sh`

---

## Development Workflow

### Local Development

1. **Setup:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Run Backend:**
   ```bash
   cd backend
   python -m app.main
   ```
   Server runs on `http://localhost:8000`

3. **Install Plugin:**
   - Copy `wordpress-plugin/smartlink-updater.php` to WordPress plugins
   - Activate in WordPress admin

### Testing

```bash
# Run all tests
python testAll.py

# Test specific extractor
python tests/test_mosttechs_extractor.py

# Test API endpoints
./test_all_endpoints.sh
```

### Deployment

```bash
# Deploy to Cloud Run
./deploy.sh

# Or manually
gcloud run deploy smartlink-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Troubleshooting

### Common Issues

1. **Post ID Not Found (404 Error)**
   - **Cause:** Wrong post ID for target site
   - **Solution:** Check `site_post_ids` mapping in config

2. **Duplicate Key Error on Fingerprints**
   - **Cause:** Old MongoDB index
   - **Solution:** Run `python backend/migrate_index.py`

3. **Extractor Not Working**
   - **Cause:** HTML structure changed
   - **Solution:** Check source monitoring, update extractor

4. **WordPress Update Fails**
   - **Cause:** Invalid credentials or permissions
   - **Solution:** Verify Application Password, check WP_SITES env var

5. **Cron Not Running**
   - **Cause:** WP-Cron disabled or not triggering
   - **Solution:** Check WordPress cron settings, use system cron if needed

---

## Support & Resources

- **GitHub:** https://github.com/Deepak22903/Smart-Link-Updater
- **Documentation:** See `/docs` folder
- **Architecture:** `ARCHITECTURE.md`
- **Multi-Site Guide:** `MULTI_SITE_SOLUTION_SUMMARY.md`
- **Extractor Guide:** `EXTRACTOR_GUIDE.md`
- **Monitoring Guide:** `MONITORING.md`

---

## Version History

- **v2.1.0** (Nov 2025) - Analytics Dashboard with charts and performance insights
- **v2.0.0** (Nov 2025) - Multi-site support, improved extractors, MongoDB migration
- **v1.5.0** (Oct 2025) - Batch updates, WordPress dashboard
- **v1.0.0** (Oct 2025) - Initial release with Gemini integration

---

## License

GPL v2 or later

---

**Last Updated:** November 9, 2025  
**Maintained By:** Deepak Shitole
