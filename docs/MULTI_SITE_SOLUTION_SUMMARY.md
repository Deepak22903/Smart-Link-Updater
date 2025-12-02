# Multi-Site Post ID Solution - Quick Start

## The Problem You Asked About

> "there is a problem regarding post id, for example the post id of the post about coin master will be different on different wp sites, how can you gracefully tackle this problem of different post ids"

## The Solution

I've implemented a **content slug + site mapping** system:

### Before (Old System):
```json
{
  "post_id": 105
}
```
❌ Problem: All sites try to update post ID 105, even if it doesn't exist

### After (New System):
```json
{
  "content_slug": "coin-master-free-spins",
  "post_id": 105,
  "site_post_ids": {
    "this": 105,
    "minecraft": 105,
    "casino": 89,
    "gaming_blog": 234
  }
}
```
✅ Solution: Each site gets the correct post ID

## What Was Changed

### Backend Files Modified:

1. **`backend/app/mongo_models.py`**
   - Added `content_slug` field (universal identifier)
   - Added `site_post_ids` dict (maps site_key → post_id)

2. **`backend/app/mongo_storage.py`**
   - Added index on `content_slug`
   - Added `get_post_config_by_slug()` function
   - Updated `set_post_config()` to use slug as primary key

3. **`backend/app/main.py`**
   - Added `resolve_post_id_for_site()` helper function
   - Updated "all sites" update logic to resolve correct post IDs
   - Updated single site update logic to resolve correct post IDs
   - Added `content_slug` and `site_post_ids` to PostConfig model

### Documentation Created:

1. **`MULTI_SITE_POST_IDS.md`** - Complete guide with:
   - Problem explanation
   - Configuration examples
   - Migration steps
   - Troubleshooting
   - Best practices

2. **`MULTI_SITE_SETUP.md`** - Guide for adding WordPress sites

## How It Works Now

### Scenario: Update "All Sites"

**Step 1**: System loads config by post ID 105:
```json
{
  "content_slug": "coin-master-free-spins",
  "site_post_ids": {
    "minecraft": 105,
    "casino": 89,
    "blog": 234
  }
}
```

**Step 2**: System extracts links once from source URLs

**Step 3**: For each site, system resolves the correct post ID:
- **minecraft** site: Uses post ID **105**
- **casino** site: Uses post ID **89**
- **blog** site: Uses post ID **234**

**Step 4**: System updates each site with its specific post ID ✅

## Next Steps to Use This Feature

### Option A: Quick Test (API)

```bash
# Update an existing post with multi-site mapping
curl -X PUT https://smartlink-api-601738079869.us-central1.run.app/config/post/105 \
  -H "Content-Type: application/json" \
  -d '{
    "content_slug": "coin-master-free-spins",
    "site_post_ids": {
      "this": 105,
      "minecraft": 105
    }
  }'

# Now when you update with target="all", it will use correct IDs
```

### Option B: Update via MongoDB

```javascript
// Connect to MongoDB Atlas
db.posts.updateOne(
  { post_id: 105 },
  { 
    $set: {
      content_slug: "coin-master-free-spins",
      site_post_ids: {
        this: 105,
        minecraft: 105,
        casino: 89
      }
    }
  }
)
```

### Option C: Add via WordPress UI (Future)

Coming soon: The "Add New Config" and "Edit" forms will have fields for entering post IDs for each site.

## Deploy the Changes

### Backend Deployment:

```bash
cd /home/deepak/data/SmartLinkUpdater/backend

# Build
docker build -t us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest .

# Push
docker push us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest

# Deploy
cd ..
gcloud run deploy smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --env-vars-file env-config.yaml \
  --port 8080
```

### WordPress Plugin:

No changes needed! The plugin already works with the new backend.

## Example Configuration

### Post: "Coin Master Free Spins" on 3 Sites

```json
{
  "content_slug": "coin-master-free-spins-2025",
  "post_id": 105,
  "site_post_ids": {
    "this": 105,
    "minecraft": 105,
    "casino": 89,
    "gaming_blog": 234
  },
  "source_urls": [
    "https://simplegameguide.com/coin-master-free-spins/"
  ],
  "extractor_map": {
    "https://simplegameguide.com/coin-master-free-spins/": "simplegameguide"
  },
  "timezone": "Asia/Kolkata"
}
```

**What happens when you click "Update All Sites":**
1. Extracts links from simplegameguide.com
2. Updates:
   - minecraftcirclegenerater.com → Post ID 105
   - casino-site.com → Post ID 89
   - gaming-blog.com → Post ID 234

## Backward Compatibility

✅ **Old configs without `site_post_ids`** still work!

If a config has:
```json
{
  "post_id": 105
}
```

The system falls back to using `post_id: 105` for all sites. This ensures existing configurations don't break.

## Finding Post IDs on Each Site

### Method 1: WordPress Admin
1. Log into each WordPress site
2. Go to **Posts → All Posts**
3. Hover over post title
4. Look at URL: `post.php?post=89` ← the number is the post ID

### Method 2: REST API
```bash
curl https://your-site.com/wp-json/wp/v2/posts?slug=coin-master-free-spins
# Returns: [{"id": 89, ...}]
```

## Summary

✅ **Problem Solved**: Different post IDs across sites  
✅ **Solution**: Content slug + site-specific post ID mapping  
✅ **Backward Compatible**: Old configs still work  
✅ **Ready to Deploy**: Code is complete and tested  
✅ **Documented**: Complete guides in `MULTI_SITE_POST_IDS.md`  

## Questions?

Refer to:
- **MULTI_SITE_POST_IDS.md** - Detailed post ID mapping guide
- **MULTI_SITE_SETUP.md** - How to add WordPress sites
- **README.md** - General project documentation

The system now gracefully handles different post IDs across multiple WordPress sites! 🎯
