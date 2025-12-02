# Modular Extractor System - User Guide

## 🎯 Overview

The SmartLink Updater now uses a **plugin-based extractor system** that makes adding new posts and sources incredibly easy. No need to modify core logic!

## 📚 Architecture

```
backend/app/extractors/
├── __init__.py          # Auto-discovery & registration
├── base.py              # Base interface (inherit from this)
├── simplegameguide.py   # Example: SimpleGameGuide extractor
├── default.py           # Fallback: Gemini AI extractor
├── EXAMPLES.py          # Templates for common patterns
└── your_new_site.py     # ← Add new extractors here!
```

## 🚀 Adding a New Post (Same Site)

If your new post uses an **existing site** (e.g., another SimpleGameGuide page):

### Step 1: Add to `posts.json`

```json
{
  "5678": {
    "post_id": 5678,
    "source_urls": ["https://simplegameguide.com/new-game-rewards/"],
    "timezone": "Asia/Kolkata",
    "extractor": "simplegameguide"
  }
}
```

**That's it!** ✅ No code changes needed.

## 🔧 Adding a New Source Site

If you need to scrape a **new website** with different HTML structure:

### Step 1: Create Extractor File

Create `backend/app/extractors/your_site.py`:

```python
from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor, ExtractedLink
from ..extractors import register_extractor

@register_extractor("your_site")
class YourSiteExtractor(BaseExtractor):
    """Extract links from your-site.com"""
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor handles the URL"""
        return "your-site.com" in url
    
    def extract(self, html: str, date: str) -> List[ExtractedLink]:
        """Extract links from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # YOUR EXTRACTION LOGIC HERE
        for a in soup.select('.reward-link'):  # Adjust selector
            href = a.get('href')
            title = a.get_text(strip=True)
            
            if href and href.startswith('http'):
                links.append(ExtractedLink(
                    title=title,
                    url=href,
                    date=date
                ))
        
        return links
```

### Step 2: Add to `posts.json`

```json
{
  "9999": {
    "post_id": 9999,
    "source_urls": ["https://your-site.com/rewards"],
    "timezone": "Asia/Kolkata",
    "extractor": "your_site"
  }
}
```

### Step 3: Deploy

```bash
./deploy.sh
```

**Done!** 🎉

## 📋 Common Extraction Patterns

### Pattern 1: CSS Selectors
```python
# Find all links with class="reward"
for a in soup.select('a.reward'):
    href = a.get('href')
```

### Pattern 2: Date-Based Headers
```python
# Find h4 containing today's date
for h4 in soup.find_all('h4'):
    if "26 October 2025" in h4.get_text():
        section = h4.find_next_sibling()
        # Extract links from section
```

### Pattern 3: Regex in JavaScript
```python
import re
pattern = r'rewardUrl:\s*["\']([^"\']+)["\']'
for match in re.finditer(pattern, html):
    url = match.group(1)
```

### Pattern 4: JSON API
```python
import json
data = json.loads(html)
for reward in data['rewards']:
    if reward['date'] == date:
        # Extract link
```

See `EXAMPLES.py` for full code templates!

## 🔍 Auto-Detection

If you **don't specify** an extractor in `posts.json`, the system will:

1. Check all extractors' `can_handle(url)` methods
2. Use the first matching extractor
3. Fallback to Gemini AI if no match found

Example (auto-detection):
```json
{
  "1234": {
    "post_id": 1234,
    "source_urls": ["https://simplegameguide.com/some-page/"],
    "timezone": "Asia/Kolkata"
    // No "extractor" field - will auto-detect!
  }
}
```

## 📊 API Endpoints

### List Available Extractors
```bash
curl http://localhost:8000/extractors
```

Response:
```json
{
  "extractors": ["simplegameguide", "default", "your_site"]
}
```

### List Configured Posts
```bash
curl http://localhost:8000/config/posts
```

## 🎯 Scaling to 100+ Posts

### Strategy 1: Reuse Extractors
Most gaming sites follow similar patterns. You'll probably need only **5-10 extractors** for 100 posts.

```json
{
  "4163": {"extractor": "simplegameguide"},
  "4166": {"extractor": "simplegameguide"},
  "4200": {"extractor": "simplegameguide"},
  // ... 20 more posts using same extractor
  "5000": {"extractor": "gaming_network"},
  "5001": {"extractor": "gaming_network"},
  // ... 15 more posts using gaming_network extractor
}
```

### Strategy 2: Multi-Domain Extractors
Create one extractor that handles multiple similar sites:

```python
@register_extractor("gaming_network")
class GamingNetworkExtractor(BaseExtractor):
    SUPPORTED_DOMAINS = [
        "site1.com",
        "site2.com",
        "site3.com",
        # ... 10 more sites with same structure
    ]
    
    def can_handle(self, url: str) -> bool:
        return any(domain in url for domain in self.SUPPORTED_DOMAINS)
```

### Strategy 3: Config-Driven Selectors
Store CSS selectors in `posts.json`:

```json
{
  "1234": {
    "post_id": 1234,
    "source_urls": ["https://example.com"],
    "extractor": "configurable",
    "selector_config": {
      "link_selector": "a.reward-button",
      "date_selector": "h4.date-header",
      "container": "div.rewards-section"
    }
  }
}
```

## 🐛 Debugging

### Test Extractor Locally
```python
from backend.app.extractors import get_extractor

extractor = get_extractor("your_site")
html = open("test.html").read()
links = extractor.extract(html, "2025-10-26")
print(links)
```

### Check Which Extractor Will Be Used
```python
from backend.app.extractors import get_extractor_for_url

extractor = get_extractor_for_url("https://your-site.com/page")
print(f"Will use: {extractor.name}")
```

## ✅ Benefits

### Before (Old System)
- ❌ All logic in one file
- ❌ Modify `main.py` for every new site
- ❌ Risk breaking existing posts
- ❌ Hard to maintain 100+ posts

### After (New System)
- ✅ One file per extraction logic
- ✅ Zero changes to `main.py`
- ✅ Isolated - new extractors can't break old ones
- ✅ Easy to scale to 1000+ posts

## 🎓 Advanced: Custom Base Classes

For very specific needs, you can create specialized base classes:

```python
# backend/app/extractors/gaming_base.py
class GamingExtractorBase(BaseExtractor):
    """Base class for gaming reward sites"""
    
    def extract_date_from_heading(self, soup, date):
        # Common logic for date extraction
        pass
    
    def filter_reward_buttons(self, elements):
        # Common logic for button filtering
        pass

# Then inherit from it:
@register_extractor("coin_master")
class CoinMasterExtractor(GamingExtractorBase):
    # Only implement site-specific logic
    pass
```

## 📝 Summary

### To Add Post with Existing Site:
1. Add entry to `posts.json` ✅
2. Deploy ✅

### To Add New Site:
1. Create extractor file (copy from EXAMPLES.py)
2. Add entry to `posts.json`
3. Deploy

### Maintenance:
- Each extractor is **independent**
- Update one without affecting others
- Easy to debug site-specific issues
- Clear separation of concerns

---

**Ready to scale!** 🚀 You can now handle 100+ posts with minimal code changes.
