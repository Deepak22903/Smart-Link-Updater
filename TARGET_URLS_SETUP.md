# Setting Up Target URLs

There are 3 ways to configure which URLs to scrape for each WordPress post:

## Method 1: CLI Tool (Easiest for Testing)

### Add a Post Configuration

```bash
# Configure post 123 to scrape Hacker News
python -m backend.app.configure_posts add 123 https://news.ycombinator.com/

# Configure post 456 to scrape multiple sources
python -m backend.app.configure_posts add 456 \
  https://news.ycombinator.com/ \
  https://lobste.rs/ \
  https://www.reddit.com/r/programming/
```

### List All Configured Posts

```bash
python -m backend.app.configure_posts list
```

### Get Configuration for Specific Post

```bash
python -m backend.app.configure_posts get 123
```

## Method 2: API Endpoints

### Configure a Post

```bash
curl -X POST http://localhost:8000/config/post \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 123,
    "source_urls": [
      "https://news.ycombinator.com/",
      "https://lobste.rs/"
    ],
    "timezone": "Asia/Kolkata"
  }'
```

### List All Posts

```bash
curl http://localhost:8000/config/posts
```

### Get Post Configuration

```bash
curl http://localhost:8000/config/post/123
```

### Trigger Update (Uses Stored Config)

```bash
# Now you can trigger without passing URLs
curl -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 123,
    "today_iso": "2025-10-26"
  }'
```

### Trigger Update (Override URLs)

```bash
# Or override the stored URLs for one-time run
curl -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 123,
    "source_urls": ["https://news.ycombinator.com/"],
    "today_iso": "2025-10-26"
  }'
```

## Method 3: Direct in Code (for MongoDB Later)

```python
from backend.app.storage import set_post_config

# Configure post 123
set_post_config(
    post_id=123,
    source_urls=[
        "https://news.ycombinator.com/",
        "https://lobste.rs/"
    ],
    timezone="Asia/Kolkata"
)
```

## Quick Start Example

### Step 1: Configure Your Posts

```bash
# Activate your venv
source env/bin/activate.fish

# Configure post 1 to scrape Hacker News
python -m backend.app.configure_posts add 1 https://news.ycombinator.com/

# Configure post 2 to scrape Lobsters
python -m backend.app.configure_posts add 2 https://lobste.rs/

# List configured posts
python -m backend.app.configure_posts list
```

### Step 2: Start the API (in one terminal)

```bash
cd /home/deepak/data/SmartLinkUpdater
source env/bin/activate.fish
uvicorn backend.app.main:app --reload
```

### Step 3: Test the Configuration

```bash
# Check health
curl http://localhost:8000/health

# List configured posts
curl http://localhost:8000/config/posts

# Trigger update for post 1
curl -X POST http://localhost:8000/trigger \
  -H 'Content-Type: application/json' \
  -d '{"post_id": 1, "today_iso": "2025-10-26"}'
```

## Common Target URLs

### Tech News
```bash
python -m backend.app.configure_posts add POST_ID \
  https://news.ycombinator.com/ \
  https://lobste.rs/ \
  https://www.reddit.com/r/programming/ \
  https://dev.to/
```

### Specific GitHub Releases/Trending
```bash
python -m backend.app.configure_posts add POST_ID \
  https://github.com/trending
```

### RSS/Atom Feeds
```bash
python -m backend.app.configure_posts add POST_ID \
  https://example.com/feed.xml
```

## Notes

- **In-Memory Storage**: Currently using in-memory storage for testing
  - Configs lost when API restarts
  - Good for development/testing
  - Replace with MongoDB for production (see `docs/data_model.md`)

- **Multiple Sources**: Each post can scrape multiple URLs
  - All links are aggregated
  - Duplicates automatically removed by fingerprint

- **Timezone**: Default is `Asia/Kolkata`
  - Customize per-post if needed
  - Controls "today" calculation

- **Target Pages**: Must have clear "Links for Today" sections
  - Or headings with today's date
  - Gemini will extract intelligently
  - Fallback parser looks for heading keywords
