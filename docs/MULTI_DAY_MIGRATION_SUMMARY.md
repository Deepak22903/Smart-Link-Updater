# Multi-Day Fingerprint Checking: Migration Summary

## What Changed

The system for handling extractors that include previous days' links has been refactored from **hardcoded checks** to a **fully modular architecture**.

## Before (Hardcoded Approach)

### Problem
- WSOP-specific logic was hardcoded in 4 different places in `main.py`
- Adding a new extractor with similar needs required modifying `main.py`
- Not maintainable or scalable
- Difficult to test individual extractors

### Code Pattern (Repeated 4 times)
```python
# Hardcoded in main.py
extractor_name = extractor.__class__.__name__.lower()
if 'wsop' in extractor_name:
    yesterday_date = datetime.strptime(today_iso, "%Y-%m-%d") - timedelta(days=1)
    yesterday_iso = yesterday_date.strftime("%Y-%m-%d")
    yesterday_fps = mongo_storage.get_known_fingerprints(
        target_post_id, yesterday_iso, target_site_key
    )
    known_fps = known_fps.union(yesterday_fps)
    print(f"[DEBUG] WSOP extractor: checking fingerprints for both {today_iso} and {yesterday_iso}")

new_links = dedupe_by_fingerprint(all_links, known_fps)
```

## After (Modular Approach)

### Solution
- Extractors declare their own lookback requirements via `check_previous_days()`
- Single reusable helper function handles all multi-day logic
- Zero changes to `main.py` when adding new extractors
- Each extractor is self-contained and testable

### 1. Extractor Declaration (wsop.py)
```python
@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    def check_previous_days(self) -> int:
        """WSOP includes yesterday's links, check today + yesterday"""
        return 1  # Check 2 days total (today + 1 previous)
    
    def extract(self, html: str, date: str) -> List[Link]:
        # Extract and mark links with correct dates
        # Yesterday's links get published_date_iso = yesterday
        # Today's links get published_date_iso = today
        return links
```

### 2. Reusable Helper (dedupe.py)
```python
def get_fingerprints_with_lookback(
    extractor: BaseExtractor,
    post_id: int,
    today_iso: str,
    site_key: str = None,
    storage_module = None
) -> Set[str]:
    """
    Automatically loads fingerprints for today and N previous days
    based on extractor.check_previous_days()
    """
    known_fps = storage_module.get_known_fingerprints(post_id, today_iso, site_key)
    
    lookback_days = extractor.check_previous_days()
    if lookback_days > 0:
        today_date = datetime.strptime(today_iso, "%Y-%m-%d")
        for i in range(1, lookback_days + 1):
            prev_date = today_date - timedelta(days=i)
            prev_iso = prev_date.strftime("%Y-%m-%d")
            prev_fps = storage_module.get_known_fingerprints(post_id, prev_iso, site_key)
            known_fps = known_fps.union(prev_fps)
    
    return known_fps
```

### 3. Clean Integration (main.py - now identical in all 4 locations)
```python
from .dedupe import get_fingerprints_with_lookback
known_fps = get_fingerprints_with_lookback(
    extractor, target_post_id, today_iso, target_site_key, mongo_storage
)
new_links = dedupe_by_fingerprint(all_links, known_fps)
```

## Files Modified

1. **`backend/app/extractors/base.py`**
   - Added `check_previous_days()` method to `BaseExtractor`
   - Default returns 0 (no lookback)
   - Extractors override to specify lookback days

2. **`backend/app/extractors/wsop.py`**
   - Overrides `check_previous_days()` to return 1
   - Documents why it needs yesterday's fingerprints

3. **`backend/app/dedupe.py`**
   - Added `get_fingerprints_with_lookback()` helper function
   - Handles all multi-day fingerprint loading logic
   - Includes logging for debugging

4. **`backend/app/main.py`**
   - Replaced 4 hardcoded WSOP checks with modular calls
   - Locations updated:
     - `/update-post/{post_id}` (line ~1217)
     - `/update-post/{post_id}` multi-site loop (line ~1412)
     - `/scrape` endpoint (line ~1616)
     - `process_post_update()` background task (line ~2019)

## Benefits

### ✅ Maintainability
- Single source of truth for multi-day logic
- Changes to fingerprint loading only need one update
- Clear separation of concerns

### ✅ Scalability
- Add unlimited extractors with different lookback requirements
- No modification to `main.py` needed
- Each extractor independently configurable

### ✅ Testability
- Test extractor's `check_previous_days()` in isolation
- Mock `get_fingerprints_with_lookback()` easily
- No coupling between extractors and main application logic

### ✅ Performance
- Extractors that don't need lookback (return 0) have zero overhead
- Only loads additional fingerprints when needed
- Efficient for both single-day and multi-day scenarios

### ✅ Developer Experience
- Self-documenting: extractor declares its needs
- Clear API: override one method
- No need to understand `main.py` internals

## Adding a New Multi-Day Extractor

**Old Way** (Don't do this):
1. Create extractor
2. Find all 4 locations in `main.py` with WSOP checks
3. Add your extractor name to each if statement
4. Hope you didn't miss any locations

**New Way** (Do this):
1. Create extractor
2. Override `check_previous_days()` to return how many days back
3. Done! ✨

```python
@register_extractor("newsite")
class NewSiteExtractor(BaseExtractor):
    def can_handle(self, url: str) -> bool:
        return "newsite.com" in url.lower()
    
    def check_previous_days(self) -> int:
        return 2  # Check today + last 2 days
    
    def extract(self, html: str, date: str) -> List[Link]:
        # Your extraction logic
        # Remember to set published_date_iso correctly!
        return links
```

## Testing

### Before: Hard to Test
```python
# Had to test entire endpoint with mock extractor
# Couldn't test deduplication logic in isolation
```

### After: Easy to Test
```python
def test_extractor_lookback():
    extractor = WSOPExtractor()
    assert extractor.check_previous_days() == 1

def test_fingerprint_loading():
    extractor = mock_extractor(lookback=2)
    fps = get_fingerprints_with_lookback(
        extractor, post_id=1, today_iso="2025-12-18",
        site_key="test", storage_module=mock_storage
    )
    # Verify 3 days were queried (today + 2 previous)
    assert mock_storage.call_count == 3
```

## Migration Checklist

- [x] Add `check_previous_days()` to `BaseExtractor`
- [x] Update WSOP extractor to use new method
- [x] Create `get_fingerprints_with_lookback()` helper
- [x] Replace hardcoded check #1 (update-post endpoint)
- [x] Replace hardcoded check #2 (multi-site loop)
- [x] Replace hardcoded check #3 (scrape endpoint)
- [x] Replace hardcoded check #4 (background task)
- [x] Test WSOP extractor still works
- [x] Create documentation
- [x] Update deployment guide

## Rollback Plan

If issues arise, the old code pattern is preserved in git history:
```bash
git log --all --grep="wsop" --oneline
git show <commit-hash>
```

## Related Documentation

- [MULTI_DAY_FINGERPRINT_CHECKING.md](./MULTI_DAY_FINGERPRINT_CHECKING.md) - Full documentation
- [EXTRACTOR_GUIDE.md](./EXTRACTOR_GUIDE.md) - Creating extractors
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
