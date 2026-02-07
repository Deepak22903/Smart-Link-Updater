# API Endpoints Reference

Complete list of all available API endpoints in the SmartLink Updater system.

## Table of Contents
- [Health & Monitoring](#health--monitoring)
- [Extractors](#extractors)
- [Post Configuration](#post-configuration)
- [WordPress Sites Management](#wordpress-sites-management)
- [Manual Links](#manual-links)
- [Update Operations](#update-operations)
- [Batch Updates](#batch-updates)
- [Alerts](#alerts)
- [Analytics](#analytics)
- [Button Styles](#button-styles)
- [Cron Settings](#cron-settings)

---

## Health & Monitoring

### `GET /health`
Basic health check endpoint to verify API is running.

**Response:**
```json
{
  "status": "ok"
}
```

### `GET /health/extractors`
Get health status of all monitored source URLs.

**Returns:** Monitoring data including:
- Status (healthy, warning, failing)
- Recent extraction statistics
- Consecutive failures
- HTML fingerprint information

### `GET /health/extractors/{source_url:path}`
Get health status for a specific source URL.

**Parameters:**
- `source_url` (path): URL-encoded source URL to check

**Returns:** Health status for the specified source

---

## Extractors

### `GET /extractors`
List all registered extractors.

**Returns:** List of available extractor names

### `GET /api/extractors/list`
Get detailed list of registered extractors with priorities.

**Returns:** Array of extractor information including:
- Name
- Priority
- Can handle domains
- Description

---

## Post Configuration

### `POST /config/post`
Configure target URLs and settings for a WordPress post.

**Request Body:**
```json
{
  "post_id": 105,
  "source_urls": ["https://example.com/page"],
  "timezone": "Asia/Kolkata",
  "content_slug": "coin-master-free-spins",
  "site_post_ids": {"site1": 105, "site2": 89},
  "extractor_map": {"https://example.com": "custom_extractor"},
  "site_ad_codes": {"default": [{"position": 1, "code": "..."}]},
  "days_to_keep": 5,
  "custom_button_title": "Get Link",
  "use_custom_button_title": false,
  "auto_update_sites": ["site1", "site2"],
  "extraction_mode": "links",
  "promo_code_section_title": "Promo Codes"
}
```

**Returns:** Success response with saved configuration

### `GET /config/posts`
List all configured posts.

**Returns:** Array of all post configurations

### `GET /config/post/{post_id}`
Get configuration for a specific post.

**Parameters:**
- `post_id` (int): WordPress post ID

**Returns:** Complete post configuration

### `PUT /config/post/{post_id}`
Update configuration for a specific post.

**Parameters:**
- `post_id` (int): WordPress post ID

**Request Body:** PostConfigUpdate object with fields to update

**Returns:** Updated configuration

### `DELETE /config/post/{post_id}`
Delete configuration for a specific post.

**Parameters:**
- `post_id` (int): WordPress post ID

**Returns:** Success confirmation

### `GET /config/sites`
Return configured WordPress sites from environment (keys and base URLs only, no credentials).

**Returns:** Dictionary of site keys with base URLs

### `GET /api/posts/list`
Get detailed list of configured posts with health status.

**Returns:** Array of posts with:
- Configuration details
- Health status
- Last check timestamp
- Last updated timestamp
- Extractor name

---

## WordPress Sites Management

### `GET /api/sites/list`
Get list of all configured WordPress sites from MongoDB.

**Returns:** Dictionary of sites with full configuration including credentials (for management UI)

### `POST /api/sites/add`
Add a new WordPress site to configuration.

**Request Body:**
```json
{
  "site_key": "my_site",
  "base_url": "https://example.com",
  "username": "admin",
  "app_password": "xxxx xxxx xxxx xxxx",
  "display_name": "My Site",
  "button_style": "default"
}
```

**Returns:** Success message with site details

### `PUT /api/sites/{site_key}`
Update an existing WordPress site configuration.

**Parameters:**
- `site_key` (string): Unique site identifier

**Request Body:** Site configuration object

**Returns:** Success message with updated details

### `DELETE /api/sites/{site_key}`
Delete a WordPress site from configuration.

**Parameters:**
- `site_key` (string): Unique site identifier

**Returns:** Success confirmation

---

## Manual Links

### `POST /api/manual-links`
Add links manually to a post.

**Request Body:**
```json
{
  "post_id": 105,
  "links": [
    {"title": "Link Title", "url": "https://example.com"}
  ],
  "date": "2025-10-26",
  "target_sites": ["site1", "site2"],
  "use_custom_button_title": false,
  "custom_button_title": "Get Link"
}
```

**Features:**
- Performs deduplication against existing links
- Updates WordPress post with new links
- Stores fingerprints for future deduplication
- Supports multi-site updates

**Returns:** Success response with:
- Links provided count
- Links added count
- Duplicates count
- Sites updated count

---

## Update Operations

### `POST /trigger`
Trigger link update for a post (legacy endpoint, used with Celery queue).

**Request Body:**
```json
{
  "post_id": 105,
  "source_urls": ["https://example.com"],
  "timezone": "Asia/Kolkata",
  "today_iso": "2025-10-26"
}
```

**Returns:** Task ID for checking status later

### `POST /update-post/{post_id}`
Trigger link update for a post with optional sync mode.

**Parameters:**
- `post_id` (int): WordPress post ID

**Query Parameters:**
- `sync` (bool): If true, wait for completion and return full results (default: false)
- `target` (string): Site key to update or 'all' for all sites

**Modes:**
- **Async (default)**: Returns immediately, runs in background
- **Sync**: Waits for completion, returns full results (used by WordPress plugin)

**Returns:**
- Async: Task ID and status URL
- Sync: Complete update results with links added

### `GET /task-status/{task_id}`
Check the status of a background task.

**Parameters:**
- `task_id` (string): Task identifier returned by `/update-post`

**Returns:** Detailed task status including:
- Post ID
- Status (running/completed/failed)
- Results for each source URL
- Errors if any

---

## Batch Updates

### `POST /api/batch-update`
Start batch update for multiple posts with progress tracking.

**Request Body:**
```json
{
  "post_ids": [105, 4163],
  "sync": false,
  "initiator": "wp-plugin",
  "target": "all"
}
```

**Parameters:**
- `post_ids`: Array of post IDs to update
- `sync`: If true, wait for completion (default: false)
- `initiator`: Source of the request (default: "wp-plugin")
- `target`: Site key or 'all' for all configured sites

**Returns:** Request ID for polling status endpoint

### `GET /api/batch-status/{request_id}`
Get current status of batch update with per-post progress.

**Parameters:**
- `request_id` (string): Request ID from `/api/batch-update`

**Returns:** Batch status including:
- Overall status
- Total posts
- Completed/successful/failed counts
- Per-post progress and logs

### `GET /api/batch-logs/{request_id}/{post_id}`
Get logs for specific post in batch update.

**Parameters:**
- `request_id` (string): Batch request ID
- `post_id` (int): Post ID

**Query Parameters:**
- `tail` (int): Number of log lines to return (default: 50, 0 for all)

**Returns:** Array of log messages for the post

### `GET /api/batch-history`
Get paginated batch update history.

**Query Parameters:**
- `limit` (int): Max results per page (default: 50)
- `skip` (int): Number of results to skip (default: 0)

**Returns:** Paginated list of batch requests with:
- Request ID
- Timestamps
- Overall status
- Post counts
- Success/failure statistics

---

## Alerts

### `GET /alerts`
Get recent alerts from the monitoring system.

**Query Parameters:**
- `hours` (int): Number of hours to look back (default: 24)

**Returns:** Array of alerts with alert details

### `GET /alerts/unnotified`
Get alerts that haven't been sent yet.

**Returns:** Array of unnotified alerts

### `POST /alerts/send`
Process and send all unnotified alerts.

**Use cases:**
- Manual testing of notification system
- Cron job to periodically check and send alerts
- Webhook trigger from Cloud Scheduler

**Returns:** Result summary with emails sent count

---

## Analytics

### `GET /api/analytics/dashboard`
Get dashboard summary with key metrics.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:**
- Total updates and success rate
- Total links added
- Active posts count
- Health distribution

### `GET /api/analytics/timeline`
Get timeline of updates over period.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)
- `granularity` (string): 'hourly', 'daily', or 'weekly' (default: 'daily')

**Returns:** Timeline data with success/failure counts per time period

### `GET /api/analytics/posts`
Get performance metrics per post.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:** Array of post performance data including:
- Total updates and success rate
- Links added
- Last update time

### `GET /api/analytics/sources`
Get performance metrics per source URL.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:** Array of source metrics including:
- Extraction success rate
- Links extracted
- Current health status

### `GET /api/analytics/extractors`
Get performance metrics per extractor type.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:** Array of extractor metrics including:
- Total updates and success rate
- Links extracted
- Posts using this extractor

### `GET /api/analytics/sites`
Get performance metrics per WordPress site.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:** Array of site metrics including:
- Total links added
- Unique posts updated
- Average links per post

### `GET /api/analytics/hourly-pattern`
Get update patterns by hour of day.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 7)

**Returns:** 24 data points showing update activity by hour

### `GET /api/analytics/links-trend`
Get daily trend of links added.

**Query Parameters:**
- `days` (int): Number of days to analyze (default: 30)

**Returns:** Daily data points with links added per site

---

## Button Styles

### `GET /api/button-styles`
Get all available button style templates.

**Returns:** Dictionary of all button styles with:
- Name
- Description
- CSS properties

### `GET /api/button-styles/{style_name}`
Get a specific button style by name.

**Parameters:**
- `style_name` (string): Style identifier (e.g., 'default', 'gradient_blue')

**Returns:** Button style configuration with CSS and hover properties

### `GET /api/button-styles/preview/{style_name}`
Generate preview HTML for a button style.

**Parameters:**
- `style_name` (string): Style identifier

**Returns:** HTML snippet showing the button in action

---

## Cron Settings

### `GET /api/cron/settings`
Get cron/scheduled update settings from MongoDB.

**Returns:**
```json
{
  "enabled": false,
  "schedule": "hourly",
  "target_sites": []
}
```

### `POST /api/cron/settings`
Save cron/scheduled update settings to MongoDB.

**Request Body:**
```json
{
  "enabled": true,
  "schedule": "hourly",
  "target_sites": ["site1", "site2"]
}
```

**Returns:** Success confirmation

---

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "message": "Operation completed",
  ...additional fields
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Status Codes
- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (WordPress authentication failed)
- `404`: Resource not found
- `500`: Internal server error

---

## Authentication

Most endpoints don't require authentication at the API level. WordPress site credentials are stored in the database and used when updating posts.

For WordPress updates, Application Passwords (not user passwords) must be configured in the Sites management interface.

---

## Rate Limiting

- Batch updates process 3 posts concurrently (configurable via semaphore)
- Background tasks run asynchronously to avoid blocking
- Use `sync=true` parameter sparingly for immediate results

---

## Usage Examples

### Configure a Post
```bash
curl -X POST http://localhost:8000/config/post \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 105,
    "source_urls": ["https://example.com/page"],
    "timezone": "Asia/Kolkata"
  }'
```

### Update a Post (Sync Mode)
```bash
curl -X POST http://localhost:8000/update-post/105?sync=true&target=all \
  -H 'Content-Type: application/json'
```

### Batch Update
```bash
curl -X POST http://localhost:8000/api/batch-update \
  -H 'Content-Type: application/json' \
  -d '{
    "post_ids": [105, 4163],
    "target": "all"
  }'
```

### Add Manual Links
```bash
curl -X POST http://localhost:8000/api/manual-links \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 105,
    "links": [{"title": "Link 1", "url": "https://example.com"}],
    "date": "2025-10-26",
    "target_sites": ["all"]
  }'
```

---

## Notes

- All endpoints accept and return JSON
- Timestamps are in ISO 8601 format
- URLs in path parameters must be URL-encoded
- The API is CORS-enabled for configured domains
- MongoDB is used as the primary data store
- Background tasks provide async processing for long operations
