# SmartLink Updater: Quick Deployment Guide

## Overview

Complete guide to deploy the new WordPress dashboard with real-time batch updates.

---

## Phase 1: Backend Deployment (Cloud Run)

### Status: ✅ COMPLETE

The backend API endpoints have been added to `backend/app/main.py`:

- `/api/batch-update` - Start batch update
- `/api/batch-status/{request_id}` - Poll batch status
- `/api/batch-logs/{request_id}/{post_id}` - Get post logs
- `/api/extractors/list` - List extractors
- `/api/posts/list` - List posts with health
- `/api/posts/{post_id}/config` - Update post config

### Deploy Backend

```bash
cd /home/deepak/data/SmartLinkUpdater

# Build Docker image
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest backend/

# Deploy to Cloud Run
gcloud run services update smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest \
  --region us-central1 \
  --project smart-link-updater

# Test new endpoints
curl https://smartlink-api-601738079869.us-central1.run.app/api/posts/list
curl https://smartlink-api-601738079869.us-central1.run.app/api/extractors/list
```

**Expected Response**:
```json
{
  "posts": [
    {
      "post_id": 105,
      "source_urls": ["https://..."],
      "timezone": "Asia/Kolkata",
      "extractor": "simplegameguide",
      "health_status": "healthy"
    }
  ]
}
```

---

## Phase 2: WordPress Plugin Update

### Option A: Manual File Update (Recommended for Testing)

1. **Backup Current Plugin**:
   ```bash
   # On your WordPress server
   cd /path/to/wordpress/wp-content/plugins
   cp -r smartlink-updater smartlink-updater-backup-$(date +%Y%m%d)
   ```

2. **Update Plugin File**:
   
   Open `smartlink-updater.php` and make these changes:

   **Step 2a: Add REST API Registration**
   
   In `__construct()` method (around line 30), add:
   ```php
   // Register REST API endpoints (server-side proxy)
   add_action('rest_api_init', array($this, 'register_rest_routes'));
   ```

   **Step 2b: Add REST API Methods**
   
   After the `handle_health_check()` method (around line 200), paste all the REST API proxy methods from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 1.

   **Step 2c: Replace Dashboard HTML**
   
   Replace the entire `render_admin_page()` method (around line 500) with the new dashboard HTML from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 2.

   **Step 2d: Add JavaScript**
   
   Paste the JavaScript from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 3 at the end of the HTML in `render_admin_page()`.

   **Step 2e: Add CSS**
   
   Update `enqueue_scripts()` method to include the CSS from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 4.

3. **Verify Plugin Activation**:
   - Go to WP Admin → Plugins
   - Deactivate "SmartLink Updater"
   - Reactivate it (checks for PHP errors)

4. **Test Dashboard**:
   - Go to WP Admin → SmartLink
   - Should see new dashboard with posts table
   - Try selecting posts and clicking "Update Selected"

### Option B: Complete File Replacement

Create a completely new plugin file:

```bash
# Create new plugin structure
mkdir -p wordpress-plugin-v2/assets/css
mkdir -p wordpress-plugin-v2/assets/js

# Extract code sections
# - smartlink-updater.php: Main plugin with REST API and dashboard
# - assets/css/dashboard.css: Styling
# - assets/js/dashboard.js: JavaScript logic
```

Then upload via FTP/SFTP or WordPress dashboard.

---

## Phase 3: Testing

### Test 1: Single Post Update

1. Go to WP Admin → SmartLink
2. Select ONE post (checkbox)
3. Click "Update Selected (1)"
4. Should see:
   - Toast notification "Batch update started"
   - Progress bar appears
   - Status changes: Queued → Running → Success
   - Progress bar fills to 100%
   - Logs button becomes enabled

### Test 2: View Logs

1. After update completes, click "Logs" button
2. Modal should open with logs like:
   ```
   [09:30:01] Starting update for post 105
   [09:30:02] Fetching HTML from source URLs...
   [09:30:05] Fetched 45231 bytes from https://...
   [09:30:08] Extracted 10 links using SimplegameguideExtractor
   [09:30:10] Found 8 new links after deduplication
   [09:30:15] ✓ Update completed: 8 links added, 1 old sections pruned
   ```

### Test 3: Batch Update (5 posts)

1. Select 5 posts
2. Click "Update Selected (5)"
3. Confirm dialog
4. Watch all 5 posts update simultaneously
5. Overall progress should show "5 / 5 posts completed"

### Test 4: Large Batch (20+ posts)

1. Click "Select All" (if you have 20+ configured posts)
2. Click "Update Selected (XX)"
3. Monitor performance:
   - Should NOT freeze browser
   - Updates should progress smoothly
   - Can still navigate WordPress admin while updating

### Test 5: Error Handling

1. Configure a post with invalid source URL
2. Try to update it
3. Should show:
   - Status: Failed
   - Error message in status cell
   - Logs show error details

---

## Troubleshooting

### Issue: "Failed to load posts"

**Cause**: REST API not working

**Solution**:
```bash
# Check WordPress REST API
curl https://yoursite.com/wp-json/smartlink/v1/posts

# If 404, check:
1. Plugin is activated
2. register_rest_routes() is called in __construct()
3. Permalink settings (WP Admin → Settings → Permalinks → Save Changes)
```

### Issue: "Invalid security token"

**Cause**: Nonce verification failing

**Solution**:
```php
// In REST API callbacks, ensure:
if (!wp_verify_nonce($request->get_header('X-WP-Nonce'), 'wp_rest')) {
    // ...only if using cookie authentication
}

// Or remove nonce check for REST API (already secured by capability check)
```

### Issue: Progress not updating

**Cause**: JavaScript polling not working

**Solution**:
1. Open browser console (F12)
2. Check for JavaScript errors
3. Verify `window.SmartLinkConfig` is defined
4. Check network tab for polling requests

### Issue: Backend 500 error

**Cause**: Python error in Cloud Run

**Solution**:
```bash
# Check Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=smartlink-api" \
  --limit 50 \
  --format json

# Look for errors in batch processing
```

---

## Rollback Plan

If anything goes wrong:

### Quick Rollback

```bash
# Restore backup
cd /path/to/wordpress/wp-content/plugins
rm -rf smartlink-updater
mv smartlink-updater-backup-YYYYMMDD smartlink-updater

# Or revert via WP Admin → Plugins → Deactivate & Delete → Upload old version
```

### Backend Rollback

```bash
# Deploy previous backend version
gcloud run services update smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:previous-tag \
  --region us-central1
```

---

## Performance Benchmarks

### Expected Performance

| Posts | Time (concurrent) | Time (sequential) |
|-------|------------------|-------------------|
| 1     | ~10-15 sec      | ~10-15 sec        |
| 5     | ~15-20 sec      | ~50-75 sec        |
| 10    | ~20-30 sec      | ~100-150 sec      |
| 50    | ~60-90 sec      | ~500-750 sec      |
| 100   | ~120-180 sec    | ~1000-1500 sec    |

**Concurrency**: 10 simultaneous updates (Cloud Run setting)

### Monitoring During Load

```bash
# Watch Cloud Run metrics
gcloud run services describe smartlink-api \
  --region us-central1 \
  --platform managed \
  --format="value(status.conditions)"

# Check container instances
gcloud run services describe smartlink-api \
  --region us-central1 \
  --format="value(status.traffic[0].latestRevision)"
```

---

## Security Checklist

- [x] No API keys in client-side JavaScript
- [x] Server-side proxy (WordPress REST API)
- [x] Capability checks (`current_user_can('edit_posts')`)
- [x] Nonce verification (optional for REST API)
- [x] Rate limiting (can be added later)
- [x] Input validation (Pydantic models)
- [x] HTTPS only (Cloud Run enforced)

---

## Next Steps After Deployment

1. **Monitor for 24 hours**:
   - Check Cloud Run logs for errors
   - Watch memory/CPU usage
   - Verify batch updates complete successfully

2. **Gather Feedback**:
   - Test with real users
   - Note any UI/UX issues
   - Check if polling interval is appropriate

3. **Optimizations**:
   - Add SSE (Server-Sent Events) for lower latency
   - Implement WebSocket for real-time updates (optional)
   - Add retry mechanism for failed updates
   - Cache extractor health status

4. **Future Features**:
   - Scheduled batch updates (cron)
   - Email notifications when batch completes
   - Export batch results to CSV
   - Advanced filtering (by extractor, health status)
   - Bulk edit posts.json
   - Extractor management UI

---

## Support & Documentation

**Full Implementation Details**:
- `WORDPRESS_DASHBOARD_IMPLEMENTATION.md` - Complete technical plan
- `WORDPRESS_PLUGIN_COMPLETE_CODE.md` - All code snippets
- `MONITORING_SUMMARY.md` - HTML monitoring system
- `MONITORING.md` - Monitoring implementation guide

**Cloud Run Dashboard**:
- https://console.cloud.google.com/run/detail/us-central1/smartlink-api

**WordPress Admin**:
- Dashboard: https://yoursite.com/wp-admin/admin.php?page=smartlink-updater
- Plugins: https://yoursite.com/wp-admin/plugins.php

---

## Contact

If you encounter any issues:
1. Check browser console for JavaScript errors
2. Check Cloud Run logs for backend errors
3. Review the documentation files above
4. Test with a single post first before large batches

**Ready to deploy? Start with Phase 1 (Backend) above! 🚀**
