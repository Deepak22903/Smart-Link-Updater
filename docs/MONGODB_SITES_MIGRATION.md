# MongoDB Sites Storage Migration

## Overview
Migrated WordPress sites configuration from ephemeral temp file storage (`/tmp/wp_sites_config.json`) to persistent MongoDB storage. This ensures sites configured via the WordPress plugin Sites tab persist across Cloud Run container restarts.

## Problem
Previously, WordPress sites configured through the dashboard were saved to `/tmp/wp_sites_config.json`, which gets cleared when Cloud Run containers restart. This meant users had to reconfigure their sites after every deployment or container restart.

## Solution
Implemented MongoDB-backed persistent storage with complete CRUD operations for WordPress sites.

## Implementation Details

### 1. MongoDB Storage Layer (`backend/app/mongo_storage.py`)

Added four new functions:

```python
def get_all_wp_sites() -> Dict[str, Dict[str, Any]]
def get_wp_site(site_key: str) -> Optional[Dict[str, Any]]
def set_wp_site(site_key: str, site_config: Dict[str, Any]) -> bool
def delete_wp_site(site_key: str) -> bool
```

**Key Features:**
- **Collection**: `wp_sites`
- **Index**: Unique index on `site_key` field
- **Document Structure**:
  ```json
  {
    "site_key": "primary",
    "base_url": "https://example.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx",
    "display_name": "Main Site",
    "created_at": "2025-01-15T10:30:00",
    "updated_at": "2025-01-15T10:30:00"
  }
  ```
- **Upsert Logic**: `set_wp_site()` uses upsert to handle both create and update operations
- **Timestamps**: Automatically tracks `created_at` and `updated_at` for audit trail

### 2. Site Loading Priority (`backend/app/wp.py`)

Updated `_load_wp_sites()` to prioritize storage sources:

1. **MongoDB** (primary, persistent)
2. **Temp file** (`/tmp/wp_sites_config.json` - legacy fallback)
3. **Environment variable** (`WP_SITES` - backward compatibility)

```python
def _load_wp_sites() -> Dict[str, Dict[str, Any]]:
    # Try MongoDB first (primary storage)
    mongo_sites = mongo_storage.get_all_wp_sites()
    if mongo_sites:
        logging.info(f"[SITES] Loaded {len(mongo_sites)} sites from MongoDB")
        return mongo_sites
    
    # Fallback to file storage
    # Fallback to environment variable
```

### 3. API Endpoints (`backend/app/main.py`)

All WordPress sites API endpoints now use MongoDB:

- **`POST /api/sites/add`**: Creates new site in MongoDB
- **`PUT /api/sites/{site_key}`**: Updates existing site in MongoDB
- **`DELETE /api/sites/{site_key}`**: Removes site from MongoDB
- **`GET /api/sites/list`**: Lists all sites from MongoDB (via `get_configured_wp_sites()`)

**Logging**: Added comprehensive logging for all site operations with `[SITES]` prefix

### 4. WordPress Plugin Integration

No changes required to the WordPress plugin. The existing plugin code continues to work:

- `loadAvailableSites()` calls `/api/sites/list` (now returns MongoDB data)
- Site add/update/delete operations seamlessly work with MongoDB backend
- Cron scheduled updates correctly fetch sites from API

## Migration Path

### For Existing Deployments

1. **Environment variable sites**: Will continue to work as fallback
2. **Temp file sites**: Will be read on first load
3. **New sites**: Will be saved to MongoDB automatically

### Recommended Migration Steps

1. Deploy updated code to Cloud Run
2. Sites configured in Sites tab will now persist in MongoDB
3. Optionally migrate existing environment variable sites:
   - Add them via Sites tab in WordPress plugin
   - Remove from `WP_SITES` environment variable

## Benefits

1. **Persistence**: Sites survive container restarts and redeployments
2. **Scalability**: Supports multiple Cloud Run instances with shared MongoDB
3. **Audit Trail**: Automatic `created_at`/`updated_at` timestamps
4. **UI Management**: Sites tab becomes the single source of truth
5. **Backward Compatibility**: Existing environment variable configs still work

## Testing

### Test MongoDB Connection
```bash
# In backend/ directory
python -c "from app import mongo_storage; print(mongo_storage.get_all_wp_sites())"
```

### Test Site CRUD Operations
```bash
# Add site
curl -X POST http://localhost:8000/api/sites/add \
  -H 'Content-Type: application/json' \
  -d '{
    "site_key": "test",
    "base_url": "https://test.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx",
    "display_name": "Test Site"
  }'

# List sites
curl http://localhost:8000/api/sites/list

# Update site
curl -X PUT http://localhost:8000/api/sites/test \
  -H 'Content-Type: application/json' \
  -d '{
    "base_url": "https://test.com",
    "username": "admin",
    "app_password": "xxxx xxxx xxxx xxxx",
    "display_name": "Updated Test Site"
  }'

# Delete site
curl -X DELETE http://localhost:8000/api/sites/test
```

## Deployment Notes

1. **MongoDB Connection**: Ensure `MONGODB_URI` environment variable is set in Cloud Run
2. **Indexes**: Automatically created on first write to `wp_sites` collection
3. **No Downtime**: Deployment is backward compatible with existing setups
4. **Monitoring**: Check logs for `[SITES]` prefix to track site operations

## Future Enhancements

1. **Encryption**: Add field-level encryption for `app_password`
2. **Versioning**: Track site configuration history
3. **Validation**: Add schema validation for site configs
4. **API Keys**: Add API key authentication for site management endpoints
5. **Bulk Operations**: Add endpoints for bulk import/export of sites

## Files Modified

- `backend/app/mongo_storage.py`: Added CRUD functions for wp_sites
- `backend/app/wp.py`: Updated `_load_wp_sites()` to prioritize MongoDB
- `backend/app/main.py`: Updated site API endpoints to use MongoDB
- `wordpress-plugin/smartlink-updater.php`: No changes (already compatible)

## Related Documentation

- `MULTI_SITE_SETUP.md`: Multi-site configuration guide
- `DEPLOYMENT_GUIDE.md`: Production deployment steps
- `ARCHITECTURE.md`: System design overview
