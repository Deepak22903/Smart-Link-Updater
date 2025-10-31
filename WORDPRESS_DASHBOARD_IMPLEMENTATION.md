# SmartLink Updater WordPress Dashboard - Complete Implementation Plan

## Executive Summary

This document provides a complete, production-ready plan to upgrade the SmartLink Updater WordPress plugin admin dashboard with:
- Real-time batch/single update progress tracking
- Live log streaming
- Extractor management
- posts.json editor
- Server-side security proxy (no client-side secrets)

**Estimated Timeline**: 2-3 days for implementation + 1 day testing
**Files to Modify**: 5 backend files, 1 plugin file, 3 new asset files
**Deployment**: Plugin update only (no backend rebuild needed initially)

---

## Phase 1: Backend API Enhancements

### 1.1 New Backend Files

#### File: `backend/app/batch_manager.py` ✅ CREATED
**Purpose**: Track batch update requests and individual post states
**Status**: Already created above

**Key Classes**:
- `UpdateStatus`: Enum (queued, running, success, partial, failed)
- `PostUpdateState`: Single post state with progress, logs, timing
- `BatchUpdateRequest`: Collection of posts with overall status
- `BatchUpdateManager`: Global manager (singleton)

---

### 1.2 New API Endpoints to Add

Add these to `backend/app/main.py`:

```python
# ============================================================================
# BATCH UPDATE ENDPOINTS (WordPress Dashboard)
# ============================================================================

@app.post("/api/batch-update")
async def start_batch_update(
    request: BatchUpdateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start batch update for multiple posts.
    
    Request:
    {
        "post_ids": [105, 111, 114, 4163],
        "sync": false,
        "initiator": "wp-plugin-v1.3.0",
        "target": "this"
    }
    
    Response:
    {
        "request_id": "550e8400-e29b-41d4-a716-446655440000",
        "started_at": "2025-10-27T09:30:00+05:30",
        "total_posts": 4,
        "mode": "background"
    }
    """
    manager = get_batch_manager()
    batch_request = manager.create_request(request.post_ids, request.initiator)
    
    if request.sync:
        # Synchronous mode: wait for completion
        await process_batch_updates(batch_request.request_id, request.target)
        return {
            "request_id": batch_request.request_id,
            "started_at": batch_request.started_at,
            "total_posts": len(request.post_ids),
            "mode": "sync",
            "status": batch_request.to_dict()
        }
    else:
        # Asynchronous mode: start background task
        background_tasks.add_task(process_batch_updates, batch_request.request_id, request.target)
        return {
            "request_id": batch_request.request_id,
            "started_at": batch_request.started_at,
            "total_posts": len(request.post_ids),
            "mode": "background"
        }


@app.get("/api/batch-status/{request_id}")
async def get_batch_status(request_id: str):
    """
    Get current status of batch update.
    
    Response:
    {
        "request_id": "uuid...",
        "overall_status": "running",
        "created_at": "2025-10-27T09:30:00+05:30",
        "started_at": "2025-10-27T09:30:01+05:30",
        "completed_at": null,
        "total_posts": 4,
        "posts": {
            "105": {
                "post_id": 105,
                "status": "success",
                "progress": 100,
                "message": "Added 8 links",
                "links_found": 10,
                "links_added": 8,
                "error": null,
                "started_at": "2025-10-27T09:30:01+05:30",
                "completed_at": "2025-10-27T09:30:15+05:30",
                "log_count": 12
            },
            "111": {
                "post_id": 111,
                "status": "running",
                "progress": 60,
                "message": "Extracting links...",
                "links_found": 0,
                "links_added": 0,
                "error": null,
                "started_at": "2025-10-27T09:30:16+05:30",
                "completed_at": null,
                "log_count": 5
            }
            // ... more posts
        }
    }
    """
    manager = get_batch_manager()
    batch_request = manager.get_request(request_id)
    
    if not batch_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    return batch_request.to_dict()


@app.get("/api/batch-logs/{request_id}/{post_id}")
async def get_post_logs(request_id: str, post_id: int, tail: int = 50):
    """
    Get logs for specific post in batch update.
    
    Query params:
    - tail: number of recent log lines (default 50)
    
    Response:
    {
        "post_id": 105,
        "logs": [
            "[09:30:01] Starting update for post 105",
            "[09:30:02] Fetching from https://example.com/rewards",
            "[09:30:05] Extracted 10 links",
            "[09:30:10] Added 8 new links to WordPress",
            "[09:30:15] Update completed successfully"
        ]
    }
    """
    manager = get_batch_manager()
    state = manager.get_post_state(request_id, post_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Post state not found")
    
    return {
        "post_id": post_id,
        "logs": state.logs[-tail:] if tail > 0 else state.logs
    }


@app.get("/api/extractors/list")
async def list_available_extractors_detailed():
    """
    Get detailed list of registered extractors.
    
    Response:
    {
        "extractors": [
            {
                "name": "simplegameguide",
                "priority": 100,
                "can_handle": ["simplegameguide.com"],
                "description": "Extractor for SimpleGameGuide.com"
            },
            {
                "name": "default",
                "priority": 0,
                "can_handle": ["*"],
                "description": "Default Gemini AI extractor"
            }
        ]
    }
    """
    from .extractors import get_all_extractors
    
    extractors_info = []
    for name, extractor_class in get_all_extractors().items():
        extractor = extractor_class()
        extractors_info.append({
            "name": name,
            "priority": getattr(extractor_class, 'priority', 0),
            "can_handle": ["*"] if name == "default" else [name],
            "description": extractor.__doc__ or f"Extractor for {name}"
        })
    
    return {"extractors": extractors_info}


@app.get("/api/posts/list")
async def list_posts_detailed():
    """
    Get detailed list of configured posts with extractor info.
    
    Response:
    {
        "posts": [
            {
                "post_id": 105,
                "source_urls": ["https://example.com/rewards"],
                "timezone": "Asia/Kolkata",
                "extractor": "simplegameguide",
                "last_updated": "2025-10-27T09:00:00+05:30",
                "status": "healthy"
            }
        ]
    }
    """
    posts = list_configured_posts()
    monitor = get_monitor()
    
    detailed_posts = []
    for post in posts:
        # Get health status for first source URL
        health = None
        if post.get("source_urls"):
            source_url = post["source_urls"][0]
            health = monitor.get_source_health(source_url)
        
        detailed_posts.append({
            **post,
            "health_status": health.get("status") if health else "unknown",
            "last_check": health.get("last_check") if health else None
        })
    
    return {"posts": detailed_posts}


@app.put("/api/posts/{post_id}/config")
async def update_post_config(post_id: int, config: PostConfig):
    """
    Update configuration for a post (posts.json editor).
    
    Request:
    {
        "post_id": 105,
        "source_urls": ["https://example.com/rewards"],
        "timezone": "Asia/Kolkata",
        "extractor": "simplegameguide"
    }
    
    Response:
    {
        "success": true,
        "post_id": 105,
        "message": "Configuration updated"
    }
    """
    # Validate extractor exists
    if hasattr(config, 'extractor') and config.extractor:
        try:
            get_extractor(config.extractor)
        except:
            raise HTTPException(status_code=400, detail=f"Extractor '{config.extractor}' not found")
    
    # Save config
    set_post_config(
        post_id=post_id,
        source_urls=[str(url) for url in config.source_urls],
        timezone=config.timezone,
        extractor_name=getattr(config, 'extractor', None)
    )
    
    return {
        "success": True,
        "post_id": post_id,
        "message": "Configuration updated"
    }


# ============================================================================
# BATCH UPDATE PROCESSOR (Background Task)
# ============================================================================

async def process_batch_updates(request_id: str, target: str = "this"):
    """
    Process all posts in a batch update request.
    Runs in background or synchronously depending on request.sync.
    """
    manager = get_batch_manager()
    batch_request = manager.get_request(request_id)
    
    if not batch_request:
        return
    
    batch_request.start()
    
    # Process posts with concurrency limit (10 at a time)
    semaphore = asyncio.Semaphore(10)
    
    async def process_single_post(post_id: int):
        async with semaphore:
            await process_post_update(request_id, post_id, target)
    
    # Start all post updates
    tasks = [process_single_post(post_id) for post_id in batch_request.post_ids]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    batch_request.complete()


async def process_post_update(request_id: str, post_id: int, target: str = "this"):
    """
    Update a single post with progress tracking and logging.
    """
    manager = get_batch_manager()
    
    try:
        # Update to running
        await manager.update_post_state(
            request_id, post_id,
            status=UpdateStatus.RUNNING,
            progress=0,
            message="Starting update",
            log_message=f"Starting update for post {post_id}"
        )
        
        # Get post config
        config = get_post_config(post_id)
        if not config:
            raise Exception(f"Post {post_id} not configured")
        
        source_urls = config.get("source_urls", [])
        timezone = config.get("timezone", "Asia/Kolkata")
        extractor_name = config.get("extractor")
        
        await manager.update_post_state(
            request_id, post_id,
            progress=10,
            message="Configuration loaded",
            log_message=f"Source URLs: {', '.join(source_urls)}"
        )
        
        # Determine today's date
        tz = pytz.timezone(timezone)
        today = datetime.now(tz)
        today_iso = today.strftime("%Y-%m-%d")
        
        # Extract links
        await manager.update_post_state(
            request_id, post_id,
            progress=20,
            message="Fetching HTML",
            log_message="Fetching HTML from source URLs..."
        )
        
        all_links = []
        for url in source_urls:
            html = await fetch_html(url)
            
            await manager.update_post_state(
                request_id, post_id,
                progress=40,
                message=f"Extracting links from {url[:50]}...",
                log_message=f"Fetched {len(html)} bytes from {url}"
            )
            
            # Choose extractor
            if extractor_name:
                extractor = get_extractor(extractor_name)
            else:
                extractor = get_extractor_for_url(url)
            
            links = extractor.extract(html, today_iso)
            all_links.extend(links)
            
            await manager.update_post_state(
                request_id, post_id,
                progress=60,
                message=f"Extracted {len(links)} links",
                log_message=f"Extracted {len(links)} links using {extractor.name} extractor"
            )
        
        if not all_links:
            await manager.update_post_state(
                request_id, post_id,
                status=UpdateStatus.SUCCESS,
                progress=100,
                message="No new links found",
                links_found=0,
                links_added=0,
                log_message="No links found for today"
            )
            return
        
        # Deduplicate
        await manager.update_post_state(
            request_id, post_id,
            progress=70,
            message="Deduplicating links",
            log_message=f"Deduplicating {len(all_links)} links..."
        )
        
        known_fps = get_known_fingerprints(post_id, today_iso)
        new_links = dedupe_by_fingerprint(all_links, known_fps)
        
        await manager.update_post_state(
            request_id, post_id,
            progress=80,
            message=f"Updating WordPress ({len(new_links)} new links)",
            log_message=f"Found {len(new_links)} new links after deduplication"
        )
        
        # Update WordPress
        wp_result = await update_post_links_section(post_id, new_links, target)
        
        # Save fingerprints
        if new_links:
            new_fps = {fingerprint(link) for link in new_links}
            save_new_links(post_id, today_iso, new_fps)
        
        # Success
        await manager.update_post_state(
            request_id, post_id,
            status=UpdateStatus.SUCCESS,
            progress=100,
            message=f"Added {wp_result['links_added']} links",
            links_found=len(all_links),
            links_added=wp_result["links_added"],
            log_message=f"✓ Update completed: {wp_result['links_added']} links added, {wp_result['sections_pruned']} old sections pruned"
        )
        
    except Exception as e:
        # Failed
        await manager.update_post_state(
            request_id, post_id,
            status=UpdateStatus.FAILED,
            progress=0,
            message=f"Error: {str(e)[:100]}",
            error=str(e),
            log_message=f"✗ Update failed: {str(e)}"
        )
```

**Add to `backend/app/main.py` after existing endpoints (around line 165)**

---

## Phase 2: WordPress Plugin Update

### 2.1 WordPress Plugin Architecture

**Current**: Single file `wordpress-plugin/smartlink-updater.php`
**New Structure**:
```
wordpress-plugin/
├── smartlink-updater.php          # Main plugin file (updated)
├── assets/
│   ├── css/
│   │   └── dashboard.css          # New dashboard styles
│   ├── js/
│   │   ├── dashboard.js           # New dashboard logic
│   │   └── batch-update.js        # Batch update handler
│   └── images/
│       └── spinner.svg            # Loading spinner
```

### 2.2 WordPress Plugin: REST API Proxy

**Add to `smartlink-updater.php` in `__construct()` method**:

```php
// Register REST API endpoints (server-side proxy)
add_action('rest_api_init', array($this, 'register_rest_routes'));
```

**Add new method to class**:

```php
/**
 * Register REST API routes (server-side proxy to Cloud Run)
 */
public function register_rest_routes() {
    // Batch update endpoint
    register_rest_route('smartlink/v1', '/batch-update', array(
        'methods' => 'POST',
        'callback' => array($this, 'handle_batch_update_rest'),
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
    
    // Batch status endpoint
    register_rest_route('smartlink/v1', '/batch-status/(?P<request_id>[a-zA-Z0-9-]+)', array(
        'methods' => 'GET',
        'callback' => array($this, 'handle_batch_status_rest'),
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
    
    // Post logs endpoint
    register_rest_route('smartlink/v1', '/batch-logs/(?P<request_id>[a-zA-Z0-9-]+)/(?P<post_id>\d+)', array(
        'methods' => 'GET',
        'callback' => array($this, 'handle_batch_logs_rest'),
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
    
    // List posts endpoint
    register_rest_route('smartlink/v1', '/posts', array(
        'methods' => 'GET',
        'callback' => array($this, 'handle_list_posts_rest'),
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
    
    // List extractors endpoint
    register_rest_route('smartlink/v1', '/extractors', array(
        'methods' => 'GET',
        'callback' => array($this, 'handle_list_extractors_rest'),
        'permission_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
}

/**
 * Handle batch update REST request (server-side proxy)
 */
public function handle_batch_update_rest($request) {
    $post_ids = $request->get_param('post_ids');
    $sync = $request->get_param('sync') ?: false;
    $target = $request->get_param('target') ?: 'this';
    
    if (empty($post_ids) || !is_array($post_ids)) {
        return new WP_Error('invalid_post_ids', 'Invalid post_ids parameter', array('status' => 400));
    }
    
    // Call Cloud Run API (server-side)
    $api_url = $this->api_base_url . '/api/batch-update';
    
    $response = wp_remote_post($api_url, array(
        'timeout' => 60,
        'headers' => array('Content-Type' => 'application/json'),
        'body' => json_encode(array(
            'post_ids' => $post_ids,
            'sync' => $sync,
            'initiator' => 'wp-plugin-v1.3.0',
            'target' => $target
        ))
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    return rest_ensure_response($data);
}

/**
 * Handle batch status REST request (server-side proxy)
 */
public function handle_batch_status_rest($request) {
    $request_id = $request->get_param('request_id');
    
    // Call Cloud Run API (server-side)
    $api_url = $this->api_base_url . '/api/batch-status/' . urlencode($request_id);
    
    $response = wp_remote_get($api_url, array(
        'timeout' => 10
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    return rest_ensure_response($data);
}

/**
 * Handle batch logs REST request (server-side proxy)
 */
public function handle_batch_logs_rest($request) {
    $request_id = $request->get_param('request_id');
    $post_id = $request->get_param('post_id');
    $tail = $request->get_param('tail') ?: 50;
    
    // Call Cloud Run API (server-side)
    $api_url = $this->api_base_url . '/api/batch-logs/' . urlencode($request_id) . '/' . intval($post_id) . '?tail=' . intval($tail);
    
    $response = wp_remote_get($api_url, array(
        'timeout' => 10
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    return rest_ensure_response($data);
}

/**
 * Handle list posts REST request (server-side proxy)
 */
public function handle_list_posts_rest($request) {
    $api_url = $this->api_base_url . '/api/posts/list';
    
    $response = wp_remote_get($api_url, array(
        'timeout' => 10
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    return rest_ensure_response($data);
}

/**
 * Handle list extractors REST request (server-side proxy)
 */
public function handle_list_extractors_rest($request) {
    $api_url = $this->api_base_url . '/api/extractors/list';
    
    $response = wp_remote_get($api_url, array(
        'timeout' => 10
    ));
    
    if (is_wp_error($response)) {
        return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
    }
    
    $body = wp_remote_retrieve_body($response);
    $data = json_decode($body, true);
    
    return rest_ensure_response($data);
}
```

---

### 2.3 WordPress Plugin: Dashboard HTML

**Replace the `render_admin_page()` method HTML with**:

(File too large to include here - see next document for complete dashboard HTML)

---

## Security Implementation

### Rate Limiting
```php
// Add to plugin class
private $rate_limit_transient_prefix = 'slu_rate_limit_';
private $rate_limit_max_requests = 10; // per hour
private $rate_limit_window = 3600; // 1 hour

private function check_rate_limit($user_id) {
    $transient_key = $this->rate_limit_transient_prefix . $user_id;
    $requests = get_transient($transient_key) ?: 0;
    
    if ($requests >= $this->rate_limit_max_requests) {
        return false;
    }
    
    set_transient($transient_key, $requests + 1, $this->rate_limit_window);
    return true;
}
```

### Nonce Validation
```php
// Add to REST callbacks
if (!wp_verify_nonce($request->get_header('X-WP-Nonce'), 'wp_rest')) {
    return new WP_Error('invalid_nonce', 'Invalid security token', array('status' => 403));
}
```

---

## Deployment Plan

### Step 1: Deploy Backend Changes
```bash
# Build new image
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest

# Deploy to Cloud Run
gcloud run services update smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest \
  --region us-central1
```

### Step 2: Deploy Plugin Changes
```bash
# Upload plugin file to WordPress
# OR
# If using Git deployment:
cp wordpress-plugin/smartlink-updater.php /path/to/wp-content/plugins/smartlink-updater/
cp -r wordpress-plugin/assets /path/to/wp-content/plugins/smartlink-updater/
```

### Step 3: Test
- Visit WP Admin → SmartLink Updater
- Test single update
- Test batch update (2-3 posts)
- Test progress tracking
- Test logs viewing

---

## Testing Checklist

- [ ] Single post update works
- [ ] Batch update (5 posts) works
- [ ] Progress bars update in real-time
- [ ] Logs appear correctly
- [ ] Error handling displays properly
- [ ] Rate limiting works (try 11 requests in 1 hour)
- [ ] Non-admin users cannot access
- [ ] CORS/security: no secrets exposed in browser
- [ ] Mobile responsive (test on phone)
- [ ] Works in Chrome, Firefox, Safari

---

## Estimated Impact

**Before**:
- Manual single-post updates only
- No progress visibility
- No batch operations
- No real-time feedback

**After**:
- Batch update 100 posts in ~2 minutes (with 10 concurrent workers)
- Real-time progress tracking
- Live log viewing
- Professional dashboard UI
- Extractor management
- posts.json editing

---

## Next Steps

1. Review this plan
2. Decide: Full implementation or phased rollout?
3. I can provide:
   - Complete dashboard HTML/CSS/JS files
   - Full plugin PHP code
   - Deployment scripts
   - Testing procedures

**Would you like me to proceed with creating the complete files?**
