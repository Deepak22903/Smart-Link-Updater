# API Documentation

## Base URL
- **Local Development:** `http://localhost:8000`
- **Production (Cloud Run):** `https://your-service.run.app`

## Endpoints

### 1. Health Check
Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "ok"
}
```

---

### 2. List Configured Posts
Get all posts that have been configured with source URLs.

**Endpoint:** `GET /config/posts`

**Response:**
```json
{
  "posts": [
    {
      "post_id": 4166,
      "source_urls": ["https://simplegameguide.com/coin-master-free-spins-links/"],
      "timezone": "Asia/Kolkata"
    }
  ]
}
```

---

### 3. Get Post Configuration
Get configuration for a specific post.

**Endpoint:** `GET /config/post/{post_id}`

**Parameters:**
- `post_id` (path): WordPress post ID

**Response:**
```json
{
  "post_id": 4166,
  "source_urls": ["https://simplegameguide.com/coin-master-free-spins-links/"],
  "timezone": "Asia/Kolkata"
}
```

**Error (404):**
```json
{
  "detail": "Post 4166 not configured"
}
```

---

### 4. Configure Post
Set up source URLs for a WordPress post.

**Endpoint:** `POST /config/post`

**Request Body:**
```json
{
  "post_id": 4166,
  "source_urls": ["https://simplegameguide.com/coin-master-free-spins-links/"],
  "timezone": "Asia/Kolkata"
}
```

**Response:**
```json
{
  "success": true,
  "post_id": 4166,
  "source_urls": ["https://simplegameguide.com/coin-master-free-spins-links/"],
  "timezone": "Asia/Kolkata"
}
```

---

### 5. Update Post Links (Main Endpoint)
**This is the endpoint the WordPress plugin will call.**

Triggers the full pipeline: scrape → extract → dedupe → update WordPress.

**Endpoint:** `POST /update-post/{post_id}`

**Parameters:**
- `post_id` (path): WordPress post ID

**Response (Detailed Status):**
```json
{
  "success": true,
  "post_id": 4166,
  "results": [
    {
      "url": "https://source1.com",
      "links": [
        { "title": "50 spins", "url": "https://example.com/link1" }
      ]
    },
    {
      "url": "https://source2.com",
      "links": []
    }
  ],
  "errors": [
    {
      "url": "https://source3.com",
      "error": "HTTPStatusError: 404 Not Found"
    }
  ],
  "completed_at": "2025-10-30T21:38:00.296969"
}
```

**Notes:**
- The `results` field contains the links extracted from each source URL.
- The `errors` field lists any issues encountered while processing specific URLs.
- The `completed_at` field indicates when the task finished processing.

**Response (No New Links):**
```json
{
  "success": true,
  "post_id": 4166,
  "message": "All links already exist - no duplicates added",
  "links_found": 3,
  "links_added": 0
}
```

**Response (No Links Found Today):**
```json
{
  "success": true,
  "post_id": 4166,
  "message": "No links found for today",
  "links_found": 0,
  "links_added": 0
}
```

**Error (404 - Post Not Configured):**
```json
{
  "detail": "Post 4166 not configured. Use /config/post to set it up first."
}
```

**Error (500 - Update Failed):**
```json
{
  "detail": "Update failed: [error message]"
}
```

---

## Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# List posts
curl http://localhost:8000/config/posts

# Get post config
curl http://localhost:8000/config/post/4166

# Update post
curl -X POST http://localhost:8000/update-post/4166

# Configure new post
curl -X POST http://localhost:8000/config/post \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 4167,
    "source_urls": ["https://example.com/links"],
    "timezone": "Asia/Kolkata"
  }'
```

### Using the Test Script

```bash
bash backend/scripts/test_api.sh
```

---

## WordPress Plugin Integration

The WordPress plugin will call the update endpoint like this:

```javascript
// JavaScript in WordPress admin
fetch('https://your-api.run.app/update-post/' + postId, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => {
  if (data.success) {
    alert('✅ ' + data.message + '\nLinks added: ' + data.links_added);
  } else {
    alert('❌ Update failed');
  }
})
.catch(error => {
  alert('❌ Error: ' + error);
});
```

---

## Running the API

### Development
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### Production (Cloud Run)
The API will be deployed as a container and automatically scaled by Google Cloud Run.

---

## Authentication (Future)

For production, you should add authentication:

1. **API Key Header:**
   ```python
   from fastapi import Header, HTTPException
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

2. **WordPress Plugin:**
   ```javascript
   headers: {
     'X-API-Key': 'your-secret-api-key'
   }
   ```

3. **Or use Cloud Run IAM authentication** (recommended for Google Cloud).
