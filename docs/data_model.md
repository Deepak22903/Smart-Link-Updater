# Data Model (MongoDB Atlas)

Use the free M0 tier and create a database named `smartlinkupdater` with the following collections:

## Collection: posts

Stores configuration per WordPress post.

```json
{
  "_id": ObjectId,
  "wp_post_id": NumberInt,
  "source_urls": ["https://example.com/page"],
  "timezone": "Asia/Kolkata",
  "created_at": ISODate,
  "updated_at": ISODate
}
```

- Index on `wp_post_id` (unique).

## Collection: runs

Audit log of each processing run.

```json
{
  "_id": ObjectId,
  "wp_post_id": NumberInt,
  "started_at": ISODate,
  "ended_at": ISODate,
  "status": "success" | "failed",
  "error": "",
  "links_added": NumberInt,
  "source_urls": ["https://example.com/page"],
  "notes": "Gemini confidence 0.82"
}
```

- Index on `wp_post_id`, `started_at` (descending) for quick history.

## Collection: link_fingerprints

Maintains idempotency per day and post.

```json
{
  "_id": ObjectId,
  "wp_post_id": NumberInt,
  "date_iso": "2025-10-26",
  "fingerprints": ["https://example.com/page__2025-10-26"],
  "updated_at": ISODate
}
```

- Compound index on (`wp_post_id`, `date_iso`) unique.

## Usage in code

- `get_known_fingerprints(post_id, date_iso)` queries `link_fingerprints` and returns the set.
- `save_new_links(...)` upserts the document, unioning the existing fingerprint array.
- `posts` determines `source_urls` and timezone (fallback to global default). Avoid passing URLs from the trigger payload in production.
- `runs` logs each job for observability and debugging.

All collections fit within M0 limits when purging older runs or aggregating monthly.
