# Multi-Day Fingerprint Checking System

## Overview

The SmartLink Updater now features a fully modular system for handling extractors that include links from previous days in their output. This prevents duplicate links from being re-added on subsequent days.

## Architecture

### 1. Base Extractor Interface

The `BaseExtractor` class now includes a `check_previous_days()` method that extractors can override:

```python
def check_previous_days(self) -> int:
    """
    Number of previous days to check when deduplicating links.
    
    Returns:
        0 = Only check today's fingerprints (default)
        1 = Check today + yesterday
        2 = Check today + yesterday + day before yesterday
        etc.
    """
    return 0  # Default behavior
```

**Location**: `backend/app/extractors/base.py`

### 2. Reusable Helper Function

A new helper function `get_fingerprints_with_lookback()` centralizes the multi-day fingerprint loading logic:

```python
def get_fingerprints_with_lookback(
    extractor: BaseExtractor,
    post_id: int,
    today_iso: str,
    site_key: str = None,
    storage_module = None
) -> Set[str]:
    """
    Automatically loads fingerprints for today and previous days based on 
    the extractor's check_previous_days() setting.
    """
```

**Location**: `backend/app/dedupe.py`

**Features**:
- Automatically queries the extractor's `check_previous_days()` method
- Loads fingerprints from today and N previous days
- Combines all fingerprints into a single set
- Logs the date range being checked for debugging

### 3. Unified Integration in main.py

All four deduplication locations in `main.py` now use the same pattern:

```python
from .dedupe import get_fingerprints_with_lookback
known_fps = get_fingerprints_with_lookback(
    extractor, target_post_id, today_iso, target_site_key, mongo_storage
)
new_links = dedupe_by_fingerprint(all_links, known_fps)
```

**Locations**:
1. `/update-post/{post_id}` endpoint (sync mode, single site)
2. `/update-post/{post_id}` endpoint (sync mode, multi-site loop)
3. `/scrape` endpoint (manual trigger)
4. `process_post_update()` background task (batch updates)

## How to Enable for Your Extractor

### Example: WSOP Extractor

The WSOP extractor includes yesterday's links in its output, so it overrides `check_previous_days()`:

```python
@register_extractor("wsop")
class WSOPExtractor(BaseExtractor):
    def can_handle(self, url: str) -> bool:
        url_lower = url.lower()
        return any(domain in url_lower for domain in [
            "wsopga.me", 
            "freechipswsop.com", 
            "wsopchipsfree.com"
        ])
    
    def check_previous_days(self) -> int:
        """
        WSOP includes yesterday's links in their daily updates,
        so check fingerprints for both today and yesterday.
        """
        return 1  # Check today + yesterday
    
    def extract(self, html: str, date: str) -> List[Link]:
        # ... extraction logic that finds both today's and yesterday's sections
        # ... marks yesterday's links with yesterday's date
        return links
```

### Creating a New Multi-Day Extractor

**Step 1**: Create your extractor class inheriting from `BaseExtractor`

```python
from .base import BaseExtractor
from ..models import Link
from ..extractors import register_extractor
from typing import List

@register_extractor("mysite")
class MySiteExtractor(BaseExtractor):
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url.lower()
    
    def check_previous_days(self) -> int:
        # Return how many days back you need to check
        return 2  # Check today + last 2 days
    
    def extract(self, html: str, date: str) -> List[Link]:
        # Your extraction logic
        # IMPORTANT: Set published_date_iso to the actual date of the link
        # Don't set all links to today's date if they're from yesterday
        links = []
        
        # Example: Extract links and mark with correct dates
        for link_data in parse_html(html):
            link = Link(
                title=link_data['title'],
                url=link_data['url'],
                date=date,  # Display date (passed parameter)
                published_date_iso=link_data['actual_date']  # Actual date for fingerprinting
            )
            links.append(link)
        
        return links
```

**Step 2**: That's it! The system automatically:
- Detects your extractor needs multi-day checking
- Loads fingerprints for the specified number of days
- Filters out duplicate links across those days
- Logs the date range being checked

## Fingerprint Format

Fingerprints use this format:
```
{url}___{published_date_iso}
```

Example:
```
https://example.com/link123___2025-12-18
```

This ensures the same URL can exist for different dates without collision.

## Benefits of This Architecture

### 1. **Zero Configuration**
- No need to modify `main.py` when adding new extractors
- No hardcoded extractor name checks
- Works automatically when extractor implements `check_previous_days()`

### 2. **Easy Maintenance**
- All multi-day logic centralized in `get_fingerprints_with_lookback()`
- Single source of truth for how many days to check
- Updates to one extractor don't affect others

### 3. **Scalability**
- Add unlimited extractors with different lookback requirements
- Each extractor independently controls its behavior
- No performance impact on extractors that don't need multi-day checking

### 4. **Debugging**
- Automatic logging of date ranges being checked
- Clear extractor class name in logs
- Easy to trace which extractor triggered multi-day checking

## Testing Your Extractor

### Unit Test Example

```python
import pytest
from backend.app.extractors.mysite import MySiteExtractor

def test_check_previous_days():
    extractor = MySiteExtractor()
    assert extractor.check_previous_days() == 2

def test_extraction_marks_correct_dates():
    extractor = MySiteExtractor()
    html = load_test_html()
    links = extractor.extract(html, "2025-12-18")
    
    # Verify yesterday's links have yesterday's date
    yesterday_links = [l for l in links if l.published_date_iso == "2025-12-17"]
    assert len(yesterday_links) > 0
    
    # Verify today's links have today's date
    today_links = [l for l in links if l.published_date_iso == "2025-12-18"]
    assert len(today_links) > 0
```

### Integration Test

```python
def test_deduplication_across_days():
    extractor = MySiteExtractor()
    
    # Simulate Day 1
    links_day1 = extractor.extract(html_day1, "2025-12-17")
    fps_day1 = {fingerprint(link) for link in links_day1}
    
    # Simulate Day 2 (includes yesterday's links)
    links_day2 = extractor.extract(html_day2, "2025-12-18")
    
    # Get fingerprints with lookback
    known_fps = get_fingerprints_with_lookback(
        extractor, post_id=123, today_iso="2025-12-18", 
        site_key="test", storage_module=mock_storage
    )
    
    # Verify deduplication works
    new_links = dedupe_by_fingerprint(links_day2, known_fps)
    assert all(link.published_date_iso == "2025-12-18" for link in new_links)
```

## Migration from Hardcoded Checks

### Before (Hardcoded)
```python
# Bad: Hardcoded extractor name checks
extractor_name = extractor.__class__.__name__.lower()
if 'wsop' in extractor_name:
    # Load yesterday's fingerprints
    yesterday_fps = mongo_storage.get_known_fingerprints(...)
    known_fps = known_fps.union(yesterday_fps)
```

### After (Modular)
```python
# Good: Automatic based on extractor's configuration
from .dedupe import get_fingerprints_with_lookback
known_fps = get_fingerprints_with_lookback(
    extractor, post_id, today_iso, site_key, mongo_storage
)
```

## Troubleshooting

### Issue: Links still being duplicated

**Check**:
1. Does your extractor override `check_previous_days()`?
2. Are you setting `published_date_iso` correctly (not all to today)?
3. Are fingerprints being saved after successful updates?

**Debug**:
```python
# Add logging in your extractor
logging.info(f"Link: {url}, Date: {published_date_iso}")

# Check fingerprints in database
fps = mongo_storage.get_known_fingerprints(post_id, date_iso, site_key)
logging.info(f"Known fingerprints: {fps}")
```

### Issue: Too many old links being filtered

**Check**:
1. Is `check_previous_days()` returning too high a number?
2. Are old fingerprints being cleaned up? (Consider adding TTL)

**Solution**:
```python
def check_previous_days(self) -> int:
    # Reduce lookback window
    return 1  # Instead of 7
```

## Performance Considerations

- Each additional day adds one MongoDB query
- Default extractors (return 0) have zero overhead
- WSOP-style extractors (return 1) add one extra query
- For extractors checking many days (3+), consider caching fingerprints

## Future Enhancements

Potential improvements to the system:

1. **Configurable Lookback**: Allow post configuration to override extractor default
2. **Smart Caching**: Cache fingerprints in memory for batch operations
3. **Fingerprint TTL**: Auto-expire fingerprints older than N days
4. **Adaptive Lookback**: Automatically adjust based on site update patterns
5. **Batch Loading**: Load all date ranges in a single query

## Related Documentation

- [EXTRACTOR_GUIDE.md](./EXTRACTOR_GUIDE.md) - Creating custom extractors
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System design overview
- [FEATURE_DOCUMENTATION.md](./FEATURE_DOCUMENTATION.md) - All features
