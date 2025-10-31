# SmartLink Updater Dashboard - Deployment Checklist

## 📋 Pre-Deployment Checklist

### Prerequisites
- [ ] Cloud Run backend is running at: `https://smartlink-api-601738079869.us-central1.run.app`
- [ ] WordPress site is accessible
- [ ] You have admin access to WordPress
- [ ] gcloud CLI is configured
- [ ] Backup of current plugin exists

---

## Phase 1: Backend Deployment

### 1.1 Verify Backend Changes
- [x] `backend/app/batch_manager.py` created (200+ lines)
- [x] `backend/app/main.py` updated with 6 new endpoints
- [x] No Python syntax errors
- [x] All imports are correct

### 1.2 Build Docker Image
```bash
cd /home/deepak/data/SmartLinkUpdater
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest backend/
```

- [ ] Build succeeds (no errors)
- [ ] Image is pushed to artifact registry
- [ ] Build time: ~5-10 minutes

### 1.3 Deploy to Cloud Run
```bash
gcloud run services update smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest \
  --region us-central1 \
  --project smart-link-updater
```

- [ ] Deployment succeeds
- [ ] Service is running
- [ ] No errors in Cloud Run logs

### 1.4 Test Backend Endpoints
```bash
# Test posts list
curl -X GET https://smartlink-api-601738079869.us-central1.run.app/api/posts/list

# Test extractors list
curl -X GET https://smartlink-api-601738079869.us-central1.run.app/api/extractors/list

# Test batch update (dry run)
curl -X POST https://smartlink-api-601738079869.us-central1.run.app/api/batch-update \
  -H "Content-Type: application/json" \
  -d '{"post_ids": [105], "sync": false, "initiator": "test", "target": "this"}'
```

**Expected Results**:
- [ ] `/api/posts/list` returns JSON with posts array
- [ ] `/api/extractors/list` returns JSON with extractors array
- [ ] `/api/batch-update` returns JSON with request_id

---

## Phase 2: WordPress Plugin Update

### 2.1 Backup Current Plugin
```bash
# On WordPress server
cd /path/to/wordpress/wp-content/plugins
cp -r smartlink-updater smartlink-updater-backup-$(date +%Y%m%d_%H%M%S)
```

- [ ] Backup created successfully
- [ ] Backup is accessible
- [ ] Backup location noted: ___________________

### 2.2 Update Plugin File

#### Step 1: Add REST API Registration
- [ ] Open `wordpress-plugin/smartlink-updater.php`
- [ ] Find `__construct()` method (around line 30)
- [ ] Add: `add_action('rest_api_init', array($this, 'register_rest_routes'));`

#### Step 2: Add REST API Methods
- [ ] Copy 6 REST API methods from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 1
- [ ] Paste after `handle_health_check()` method (around line 200)
- [ ] Methods added:
  - [ ] `register_rest_routes()`
  - [ ] `handle_batch_update_rest()`
  - [ ] `handle_batch_status_rest()`
  - [ ] `handle_batch_logs_rest()`
  - [ ] `handle_list_posts_rest()`
  - [ ] `handle_list_extractors_rest()`

#### Step 3: Update Dashboard HTML
- [ ] Find `render_admin_page()` method (around line 500)
- [ ] Replace entire HTML section with code from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 2
- [ ] Verify closing tags match

#### Step 4: Add JavaScript
- [ ] Copy JavaScript from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 3
- [ ] Paste in `<script>` tag at end of `render_admin_page()` HTML
- [ ] Verify `window.SmartLinkConfig` is defined

#### Step 5: Add CSS
- [ ] Find `enqueue_scripts()` method
- [ ] Copy CSS from `WORDPRESS_PLUGIN_COMPLETE_CODE.md` Part 4
- [ ] Add as inline style using `wp_add_inline_style()`

### 2.3 Upload to WordPress
- [ ] Upload updated `smartlink-updater.php` via FTP/SFTP
- [ ] OR upload via WP Admin → Plugins → Upload Plugin

### 2.4 Verify Plugin Activation
- [ ] Go to WP Admin → Plugins
- [ ] Check for any PHP errors (white screen = error)
- [ ] Deactivate plugin
- [ ] Reactivate plugin
- [ ] No errors displayed

---

## Phase 3: Testing

### 3.1 Load Dashboard
- [ ] Go to WP Admin → SmartLink
- [ ] Dashboard loads without errors
- [ ] Posts table appears
- [ ] Batch controls visible
- [ ] No JavaScript errors in browser console (F12)

### 3.2 Test Single Update
- [ ] Select ONE post (checkbox)
- [ ] Selected count shows "1"
- [ ] Click "Update Selected (1)"
- [ ] Confirm dialog appears
- [ ] Click OK
- [ ] Toast notification: "Batch update started"
- [ ] Progress bar appears
- [ ] Status changes: Idle → Queued → Running → Success
- [ ] Progress bar fills to 100%
- [ ] "Completed: 1 / 1 posts" shown
- [ ] Update completes in ~10-20 seconds

### 3.3 Test Logs
- [ ] Click "Logs" button for updated post
- [ ] Modal opens
- [ ] Logs appear (timestamped)
- [ ] Example log lines visible:
  ```
  [HH:MM:SS] Starting update for post XXX
  [HH:MM:SS] Fetching HTML from source URLs...
  [HH:MM:SS] Extracted X links...
  [HH:MM:SS] ✓ Update completed: X links added
  ```
- [ ] Click "Refresh" - logs reload
- [ ] Click "Close" - modal closes

### 3.4 Test Batch Update (5 posts)
- [ ] Click "Deselect All"
- [ ] Select 5 posts manually
- [ ] Selected count shows "5"
- [ ] Click "Update Selected (5)"
- [ ] Confirm dialog
- [ ] Click OK
- [ ] All 5 posts start updating
- [ ] Progress bars update for each post
- [ ] Overall progress: "5 / 5 posts completed"
- [ ] All posts complete successfully
- [ ] Time: ~20-40 seconds

### 3.5 Test Error Handling
- [ ] Configure a post with invalid URL (if possible)
- [ ] Update that post
- [ ] Status shows "Failed"
- [ ] Error message appears in status
- [ ] Logs show error details
- [ ] Other posts in batch still succeed

### 3.6 Test UI Features
- [ ] Click "Select All" - all checkboxes selected
- [ ] Click "Deselect All" - all checkboxes unselected
- [ ] Click "Refresh" - table reloads
- [ ] Click single "Update" button - single post updates
- [ ] Toast notifications work (appear and disappear)
- [ ] Progress bars animate smoothly

### 3.7 Test Mobile/Responsive
- [ ] Open dashboard on mobile device
- [ ] Layout is responsive
- [ ] Buttons are touchable
- [ ] Table is readable (may scroll horizontally)
- [ ] Modal works on mobile

---

## Phase 4: Monitoring

### 4.1 Check Cloud Run Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=smartlink-api" \
  --limit 50 \
  --format json
```

- [ ] No errors in logs
- [ ] Batch updates logged correctly
- [ ] API requests logged

### 4.2 Monitor Performance
- [ ] Cloud Run CPU usage normal (<80%)
- [ ] Cloud Run memory usage normal (<80%)
- [ ] Response times < 1 second for status polls
- [ ] No timeouts

### 4.3 Verify Data Integrity
- [ ] Check WordPress posts - links added correctly
- [ ] Check `backend/data/posts.json` - configuration intact
- [ ] Check `backend/data/fingerprints.json` - new fingerprints saved
- [ ] Check `backend/data/monitoring.json` - monitoring data updated

---

## Phase 5: Rollback (If Needed)

### 5.1 Plugin Rollback
```bash
cd /path/to/wordpress/wp-content/plugins
rm -rf smartlink-updater
mv smartlink-updater-backup-TIMESTAMP smartlink-updater
```

- [ ] Backup restored
- [ ] Plugin reactivated
- [ ] Old dashboard works

### 5.2 Backend Rollback
```bash
# Find previous revision
gcloud run revisions list --service=smartlink-api --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic smartlink-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1
```

- [ ] Traffic routed to old revision
- [ ] Old API endpoints work
- [ ] No errors

---

## Phase 6: Production Monitoring (First 24 Hours)

### Hour 1
- [ ] Check for immediate errors
- [ ] Verify 1-2 batch updates work
- [ ] Monitor Cloud Run logs

### Hour 6
- [ ] Check Cloud Run metrics
- [ ] Review any error logs
- [ ] Verify multiple users can update

### Hour 24
- [ ] Review full day of logs
- [ ] Check for any performance issues
- [ ] Gather user feedback

---

## Success Criteria

### Functional
- ✅ Batch updates work for 1-100 posts
- ✅ Progress tracking updates in real-time
- ✅ Logs are viewable and accurate
- ✅ Error handling works correctly
- ✅ UI is responsive and user-friendly

### Performance
- ✅ 1 post updates in ~10-20 seconds
- ✅ 10 posts update in ~20-40 seconds (concurrent)
- ✅ 100 posts update in ~2-3 minutes (concurrent)
- ✅ Browser does not freeze during updates
- ✅ Polling does not cause performance issues

### Security
- ✅ No API keys exposed in browser
- ✅ Only authorized users can update
- ✅ Server-side proxy works correctly
- ✅ HTTPS is enforced

### Reliability
- ✅ No errors in Cloud Run logs
- ✅ No JavaScript errors in browser console
- ✅ Updates complete consistently
- ✅ Retry/error recovery works

---

## Issue Tracking

### Issues Found During Testing

| Issue | Severity | Status | Solution |
|-------|----------|--------|----------|
| Example: Progress not updating | High | 🔴 Open | Check polling interval |
| | | | |
| | | | |

---

## Sign-Off

### Backend Deployment
- [ ] Backend deployed successfully
- [ ] All API endpoints tested
- [ ] No errors in logs
- **Deployed by**: ________________
- **Date**: ________________
- **Backend URL**: https://smartlink-api-601738079869.us-central1.run.app

### WordPress Plugin Update
- [ ] Plugin updated successfully
- [ ] All features tested
- [ ] No errors in WordPress
- **Updated by**: ________________
- **Date**: ________________
- **WordPress URL**: ________________

### Final Approval
- [ ] All tests passed
- [ ] No critical issues found
- [ ] Ready for production use
- **Approved by**: ________________
- **Date**: ________________

---

## Quick Reference

**Documentation**:
- Implementation Plan: `WORDPRESS_DASHBOARD_IMPLEMENTATION.md`
- Complete Code: `WORDPRESS_PLUGIN_COMPLETE_CODE.md`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Summary: `IMPLEMENTATION_SUMMARY.md`

**Commands**:
```bash
# Deploy backend
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest backend/
gcloud run services update smartlink-api --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest --region us-central1

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=smartlink-api" --limit 50

# Rollback
gcloud run services update-traffic smartlink-api --to-revisions=PREVIOUS_REVISION=100 --region=us-central1
```

**Support**:
- Cloud Run Console: https://console.cloud.google.com/run/detail/us-central1/smartlink-api
- WordPress Admin: https://yoursite.com/wp-admin/admin.php?page=smartlink-updater

---

**Ready to deploy? Start with Phase 1! 🚀**
