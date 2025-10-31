# Multi-Site Support

The SmartLinkUpdater now supports updating posts on **multiple WordPress sites**, not just the default site configured in `.env`.

## Default Site (Environment Variables)

By default, all posts use the WordPress credentials from `.env`:

```env
WP_BASE_URL=https://minecraftcirclegenerater.com
WP_USERNAME=deepakshitole4@gmail.com
WP_APPLICATION_PASSWORD=T3IpO84Qjg6hFSokpOP3ADZl
```

## Custom Site Per Post

You can override these settings for individual posts by including `wp_site` in the post configuration:

### API Example

```bash
curl -X POST "http://localhost:8000/config/post" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 888,
    "source_urls": ["https://simplegameguide.com/coin-master-free-spins-links/"],
    "timezone": "America/New_York",
    "wp_site": {
      "base_url": "https://your-second-site.com",
      "username": "admin@example.com",
      "app_password": "xxxx xxxx xxxx xxxx"
    }
  }'
```

### Manual Configuration (posts.json)

You can also edit `backend/data/posts.json` directly:

```json
{
  "888": {
    "post_id": 888,
    "source_urls": [
      "https://simplegameguide.com/coin-master-free-spins-links/"
    ],
    "timezone": "America/New_York",
    "wp_site": {
      "base_url": "https://your-second-site.com",
      "username": "admin@example.com",
      "app_password": "xxxx xxxx xxxx xxxx"
    }
  },
  "999": {
    "post_id": 999,
    "source_urls": [
      "https://simplegameguide.com/carnival-tycoon-free-spins/"
    ],
    "timezone": "Asia/Kolkata"
    // No wp_site - uses default from .env
  }
}
```

## Use Cases

### 1. Multiple WordPress Sites
Update posts on different WordPress installations:
- Site A: `minecraftcirclegenerater.com` (default)
- Site B: `your-gaming-blog.com` (custom per post)
- Site C: `another-site.com` (custom per post)

### 2. Different User Permissions
Use different WordPress accounts with different permissions:
- Admin account for important posts
- Editor account for regular updates

### 3. Staging vs Production
Test on staging before deploying to production:
- Post 100: Staging site (for testing)
- Post 200: Production site (live updates)

## Update Process

When you run an update, the system:

1. **Loads post configuration** from `posts.json`
2. **Checks for `wp_site`** field
3. **Uses custom site** if specified, otherwise uses `.env` defaults
4. **Authenticates** with the appropriate credentials
5. **Updates the post** on the target WordPress site

Example update:

```bash
# Post 888 will update on your-second-site.com
curl -X POST "http://localhost:8000/update-post/888?sync=true"

# Post 999 will update on minecraftcirclegenerater.com (default)
curl -X POST "http://localhost:8000/update-post/999?sync=true"
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit `posts.json` to public repos** if it contains credentials
2. **Use Application Passwords**, not regular WordPress passwords
3. **Restrict API access** using firewall rules or authentication
4. **Consider Secret Manager** for production (Google Cloud Secret Manager, AWS Secrets Manager)

### Recommended: Use Environment Variables for Multiple Sites

Instead of hardcoding credentials in `posts.json`, use environment variables:

Option A — Single env vars for default site (legacy):

```env
# Default site
WP_BASE_URL=https://minecraftcirclegenerater.com
WP_USERNAME=deepakshitole4@gmail.com
WP_APPLICATION_PASSWORD=xxxx
```

Option B — Recommended: provide a JSON map of additional sites using `WP_SITES` env var.
This lets you centrally configure many sites in one env variable (or via Secret Manager).

Example `.env` snippet:

```env
# JSON-encoded map of site_key -> site config
WP_SITES='{
  "site_b": {
    "base_url": "https://your-second-site.com",
    "username": "admin@example.com",
    "app_password": "yyyy"
  },
  "site_c": {
    "base_url": "https://another-site.com",
    "username": "editor@another.com",
    "app_password": "zzzz"
  }
}'
```

The backend exposes a safe endpoint `/config/sites` that returns the available `site_key -> base_url` mapping for the plugin UI to show.

Use Secret Manager or your deployment system to inject `WP_SITES` securely (do not commit to repo).

## Cloud Deployment

When deploying to Google Cloud Run:

### Option 1: Environment Variables
Set multiple site credentials as environment variables in Cloud Run.

### Option 2: Secret Manager
Store credentials in Google Secret Manager and reference them:

```bash
gcloud run services update smartlink-api \
  --update-secrets=WP_BASE_URL=wp_base_url:latest \
  --update-secrets=WP_USERNAME=wp_username:latest \
  --update-secrets=WP_APPLICATION_PASSWORD=wp_app_password:latest \
  --update-secrets=WP_SITE_B_BASE_URL=wp_site_b_base_url:latest
```

## Testing

Test the multi-site feature:

```bash
# 1. Configure a test post
python3 example_multisite.py

# 2. Verify configuration
curl -s "http://localhost:8000/config/post/888" | python3 -m json.tool

# 3. Test update (use sync=true for immediate results)
curl -s -X POST "http://localhost:8000/update-post/888?sync=true" | python3 -m json.tool
```

## Summary

✅ **Supported:** Update posts on unlimited WordPress sites  
✅ **Per-Post Configuration:** Each post can target a different site  
✅ **Backward Compatible:** Existing posts use default `.env` credentials  
✅ **Flexible:** Mix default and custom sites in the same deployment  
