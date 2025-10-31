# MongoDB Integration Notes

- Use `motor` (async MongoDB driver) to avoid blocking the FastAPI event loop and Celery worker.
- Create a singleton `AsyncIOMotorClient` and reuse across tasks.
- Suggested helpers:
  - `async def get_post_config(post_id: int) -> dict`
  - `async def upsert_link_fingerprints(post_id: int, date_iso: str, new_fps: set[str])`
- Add indexes:

```python
await db.link_fingerprints.create_index(
    [("wp_post_id", 1), ("date_iso", 1)], unique=True
)
```

- For tests, use `mongomock` or a local container.
- Keep fingerprint documents under 16 MB by trimming old entries (set per day).
