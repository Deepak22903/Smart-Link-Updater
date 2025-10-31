# Deduplication System

## Overview
The SmartLinkUpdater uses fingerprint-based deduplication to prevent adding the same links multiple times to WordPress posts.

## How It Works

### 1. Fingerprint Generation
Each link is converted to a unique fingerprint:
```
fingerprint = URL + "|||" + DATE
Example: "https://rewards.coinmaster.com/...|||2025-10-26"
```

### 2. Storage
Fingerprints are stored in `backend/data/fingerprints.json`:
```json
{
  "4166_2025-10-26": [
    "https://rewards.coinmaster.com/...|||2025-10-26",
    "https://rewards.coinmaster.com/...|||2025-10-26"
  ]
}
```

Key format: `{post_id}_{date_iso}`

### 3. Deduplication Flow

```
1. Scrape target URLs
2. Extract links for today
3. Get known fingerprints for (post_id, date)
4. Filter out links that match known fingerprints
5. Update WordPress with only NEW links
6. Save new fingerprints to storage
```

## Example Test Results

### First Run:
```
🔍 Step 3.5: Checking for duplicates...
   Known fingerprints: 0
   New links after deduplication: 3
   ✅ Post updated successfully!
   ✅ Saved 3 fingerprints
```

### Second Run (same day):
```
🔍 Step 3.5: Checking for duplicates...
   Known fingerprints: 3
   New links after deduplication: 0
   ⚠️  All links already exist - nothing to update
```

## Files Involved

- `backend/app/dedupe.py` - Core deduplication logic
- `backend/app/storage.py` - Fingerprint persistence
  - `get_known_fingerprints(post_id, date_iso)` - Load existing fingerprints
  - `save_new_links(post_id, date_iso, fingerprints)` - Save new fingerprints
- `backend/app/tasks.py` - Celery task with deduplication integrated
- `backend/data/fingerprints.json` - Storage file (auto-created)

## Benefits

✅ **No Duplicates:** Same link can't be added twice on the same day
✅ **Date-Specific:** Links from different days are tracked separately
✅ **Post-Specific:** Each post has its own fingerprint tracking
✅ **Automatic:** Runs automatically during every update
✅ **Efficient:** Quick hash-based lookup

## Testing

Run the test script twice to verify:
```bash
# First run - adds links
python backend/scripts/test_full_pipeline.py

# Second run - skips existing links
python backend/scripts/test_full_pipeline.py
```

## Migration to MongoDB

When moving to MongoDB Atlas, the fingerprints will be stored in a collection:
```javascript
{
  _id: ObjectId("..."),
  post_id: 4166,
  date_iso: "2025-10-26",
  fingerprints: [
    "https://rewards.coinmaster.com/...|||2025-10-26",
    "https://rewards.coinmaster.com/...|||2025-10-26"
  ]
}
```

Index on: `{post_id: 1, date_iso: 1}` for fast lookups.
