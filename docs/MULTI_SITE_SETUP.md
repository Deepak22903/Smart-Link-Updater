# Multi-Site WordPress Setup Guide

## Overview
The SmartLink Updater supports updating links across multiple WordPress sites. You only need to update the `env-config.yaml` file and redeploy.

## Adding/Removing Sites

### 1. Edit `env-config.yaml`

Update the `WP_SITES` value with your WordPress sites in JSON format:

```yaml
WP_SITES: '{"site_key_1":{"base_url":"https://site1.com","username":"admin1","app_password":"xxxx"},"site_key_2":{"base_url":"https://site2.com","username":"admin2","app_password":"yyyy"}}'
```

**Format:**
- Must be valid JSON wrapped in single quotes
- Each site needs a unique key (e.g., `site_key_1`, `minecraft`, etc.)
- Each site config requires:
  - `base_url`: WordPress site URL (without trailing slash)
  - `username`: WordPress admin username or email
  - `app_password`: WordPress Application Password

**Example with 3 sites:**
```yaml
WP_SITES: '{"minecraft":{"base_url":"https://minecraftcirclegenerater.com","username":"admin@example.com","app_password":"kHZx W12R nlAp iN3F"},"casino":{"base_url":"https://casino-site.com","username":"admin@casino.com","app_password":"abcd efgh ijkl mnop"},"tech_blog":{"base_url":"https://tech-blog.com","username":"tech@blog.com","app_password":"qrst uvwx yzab cdef"}}'
```

### 2. Deploy to Cloud Run

Run the deployment command:

```bash
cd /home/deepak/data/SmartLinkUpdater
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

### 3. Verify in Dashboard

After deployment:
1. Open your WordPress dashboard
2. Go to SmartLink Updater
3. Click the "Update Target" dropdown
4. You should see:
   - **This Site** (current WordPress installation)
   - **All Sites** (updates all configured sites)
   - **minecraft** (your site key)
   - **casino** (if configured)
   - **tech_blog** (if configured)
   - etc.

## How to Get WordPress Application Password

1. Log into your WordPress site
2. Go to: **Users → Profile**
3. Scroll to **Application Passwords** section
4. Enter a name (e.g., "SmartLink API")
5. Click **Add New Application Password**
6. Copy the generated password (format: `xxxx yyyy zzzz aaaa`)
7. Paste it into `env-config.yaml` (keep or remove spaces - both work)

## Update Target Behavior

### This Site
- Updates only the WordPress site where the plugin is installed
- Uses `WP_BASE_URL`, `WP_USERNAME`, `WP_APPLICATION_PASSWORD` from env

### All Sites
- Extracts links once from source URLs
- Updates **all** sites configured in `WP_SITES`
- Most efficient for syncing across multiple sites

### Individual Site (e.g., "minecraft")
- Extracts links once
- Updates only the selected site
- Useful for testing or selective updates

## Example Workflow

### Scenario: You have 3 WordPress sites about gaming

**Step 1: Update `env-config.yaml`**
```yaml
WP_SITES: '{"minecraft_guide":{"base_url":"https://minecraftcirclegenerater.com","username":"admin@minecraft.com","app_password":"pass1"},"roblox_tips":{"base_url":"https://roblox-tips.com","username":"admin@roblox.com","app_password":"pass2"},"gaming_news":{"base_url":"https://gaming-news.com","username":"admin@gaming.com","app_password":"pass3"}}'
```

**Step 2: Deploy**
```bash
gcloud run deploy smartlink-api --env-vars-file env-config.yaml ...
```

**Step 3: Use in Dashboard**
- Select **"All Sites"** → Updates all 3 sites with same links
- Select **"minecraft_guide"** → Updates only Minecraft site
- Select **"This Site"** → Updates only the site where plugin is installed

## Troubleshooting

### Site not appearing in dropdown
- Check JSON syntax in `WP_SITES` (use a JSON validator)
- Ensure deployment succeeded
- Refresh the WordPress dashboard

### Update fails for specific site
- Verify Application Password is correct
- Check `base_url` doesn't have trailing slash
- Ensure WordPress REST API is accessible
- Check WordPress user has edit permissions

### Quick JSON Validation
Test your JSON before deploying:
```bash
echo '{"site1":{"base_url":"https://example.com","username":"admin","app_password":"pass"}}' | python3 -m json.tool
```

## Tips

1. **Use Descriptive Keys**: Name sites clearly (e.g., `minecraft_guide`, not `site1`)
2. **Keep Backup**: Save a copy of working `env-config.yaml`
3. **Test with One Site First**: Add sites gradually
4. **Monitor First Update**: Check Cloud Run logs after adding new site
5. **Application Passwords Expire**: Some hosts expire them, regenerate if needed

## Current Configuration

Your current `env-config.yaml` has:
- **Main site**: minecraftcirclegenerater.com (uses `WP_BASE_URL`)
- **Configured sites in WP_SITES**:
  - `site_test`: example-site.com (test/demo)
  - `minecraft`: minecraftcirclegenerater.com (same as main)

You can add more sites by editing the `WP_SITES` line and redeploying.
