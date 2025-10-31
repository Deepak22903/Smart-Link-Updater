# Target URL Configuration Guide

Your post configuration is now stored in: `backend/posts_config.json`

## Quick Start

### 1. Configure a WordPress Post

```bash
# Add a single source URL to post ID 4163
python -m backend.app.configure_posts add 4163 https://simplegameguide.com/carnival-tycoon-free-spins/

# Add multiple sources to a post
python -m backend.app.configure_posts add 456 \
  https://news.ycombinator.com/ \
  https://lobste.rs/ \
  https://reddit.com/r/programming/
```

### 2. List All Configured Posts

```bash
python -m backend.app.configure_posts list
```

Output:
```
Configured Posts (1):

  Post ID: 4163
  Timezone: Asia/Kolkata
  Sources:
    - https://simplegameguide.com/carnival-tycoon-free-spins/
```

### 3. View Specific Post Config

```bash
python -m backend.app.configure_posts get 4163
```

### 4. Test the Full Pipeline (Without Starting Services)

```bash
# Set your WordPress credentials first
cp .env.example .env
# Edit .env with your WP_BASE_URL, WP_USERNAME, WP_APPLICATION_PASSWORD

# Optional: Set Gemini API key for intelligent extraction
set -x GEMINI_API_KEY "your-key-here"

# Test scraping and extraction for post 4163
python -c "
import asyncio
from backend.app.tasks import update_post_task

asyncio.run(update_post_task(
    post_id=4163,
    source_urls=['https://simplegameguide.com/carnival-tycoon-free-spins/'],
    timezone='Asia/Kolkata',
    today_iso='2025-10-26'
))
"
```

## Configuration File Location

**File**: `backend/posts_config.json`

**Format**:
```json
{
  "4163": {
    "post_id": 4163,
    "source_urls": [
      "https://simplegameguide.com/carnival-tycoon-free-spins/"
    ],
    "timezone": "Asia/Kolkata"
  }
}
```

## Production Setup

### Option 1: Use Configuration File (Current)
- Configure posts via CLI
- File persists across restarts
- Simple for small deployments

### Option 2: WordPress Post Meta (Future)
- Store source URLs in WordPress custom fields
- Fetch via WP REST API at runtime
- Better for large sites with many editors

### Option 3: MongoDB Atlas (Recommended for Production)
- Implement `backend/app/storage.py` MongoDB methods
- Centralized config across multiple workers
- Audit logs and history

## Next Steps

1. **Configure Your Posts**
   ```bash
   python -m backend.app.configure_posts add <post_id> <url>
   ```

2. **Set WordPress Credentials** in `.env`:
   ```bash
   WP_BASE_URL=https://your-site.com
   WP_USERNAME=admin
   WP_APPLICATION_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```

3. **Optional: Set Gemini API Key** for intelligent extraction:
   ```bash
   set -x GEMINI_API_KEY "your-key"
   ```

4. **Start the Services**:
   ```bash
   docker compose up
   ```

5. **Trigger Update**:
   ```bash
   # Via API
   curl -X POST http://localhost:8000/trigger \
     -H 'Content-Type: application/json' \
     -d '{"post_id": 4163, "source_urls": [], "timezone": "Asia/Kolkata"}'
   
   # source_urls can be empty - will fetch from config file
   ```

## How It Works

1. **Configure** → Post ID + Source URLs saved to `posts_config.json`
2. **Trigger** → API receives post ID
3. **Fetch Config** → Reads source URLs from config file
4. **Scrape** → Fetches HTML from all source URLs
5. **Extract** → Gemini finds "Links for Today" (or fallback parser)
6. **Dedupe** → Filters duplicates and old links
7. **Update** → Posts new links to WordPress via REST API

Your post 4163 is ready to go! 🚀
