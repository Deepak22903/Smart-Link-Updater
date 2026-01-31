# Promo Code Extraction Feature

## Overview

SmartLink Updater now supports extracting **promo codes** from source sites in addition to links. This allows you to automatically update your WordPress posts with promotional codes, coupon codes, or bonus codes from gaming/reward sites.

## Configuration

### Per-Post Extraction Mode

Each post can be configured with an `extraction_mode` to determine what should be extracted:

| Mode | Description |
|------|-------------|
| `links` | Extract only links (default, backward compatible) |
| `promo_codes` | Extract only promo codes |
| `both` | Extract both links AND promo codes |

### Setting Extraction Mode via API

```bash
# Configure a post to extract promo codes
curl -X PUT http://localhost:8000/config/post/105 \
  -H 'Content-Type: application/json' \
  -d '{
    "extraction_mode": "promo_codes",
    "promo_code_section_title": "Today'\''s Bonus Codes"
  }'

# Configure for both links and promo codes
curl -X PUT http://localhost:8000/config/post/105 \
  -H 'Content-Type: application/json' \
  -d '{
    "extraction_mode": "both"
  }'
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `extraction_mode` | string | `"links"`, `"promo_codes"`, or `"both"` |
| `promo_code_section_title` | string | Custom title for the promo codes section (supports `{date}` placeholder) |

## Creating a Promo Code Extractor

To extract promo codes from a new site, create a custom extractor that implements the promo code extraction interface.

### Step 1: Create the Extractor File

Create a new file in `backend/app/extractors/` (e.g., `mysite_promo.py`):

```python
from typing import List
from bs4 import BeautifulSoup
from .base import BaseExtractor
from ..models import Link, PromoCode
import re


def register_extractor(name):
    def decorator(cls):
        cls._extractor_name = name
        return cls
    return decorator


@register_extractor("mysite")
class MySiteExtractor(BaseExtractor):
    """Extractor for mysite.com promo codes."""
    
    def can_handle(self, url: str) -> bool:
        return "mysite.com" in url.lower()
    
    def supports_promo_codes(self) -> bool:
        """Return True to enable promo code extraction."""
        return True
    
    def extract(self, html: str, date: str) -> List[Link]:
        """Extract links (implement if needed)."""
        return []  # Return empty if only extracting promo codes
    
    def extract_promo_codes(self, html: str, date: str) -> List[PromoCode]:
        """Extract promo codes from the page."""
        soup = BeautifulSoup(html, 'html.parser')
        codes = []
        
        # Example: Find codes in <code> tags within promo containers
        for container in soup.find_all('div', class_='promo-code'):
            code_elem = container.find('code')
            if code_elem:
                code = code_elem.get_text(strip=True)
                desc = container.find('p')
                description = desc.get_text(strip=True) if desc else None
                
                codes.append(PromoCode(
                    code=code,
                    description=description,
                    published_date_iso=date,
                    category="bonus"
                ))
        
        return codes
```

### Step 2: Configure the Post

```json
{
  "post_id": 200,
  "source_urls": ["https://mysite.com/promo-codes/"],
  "timezone": "Asia/Kolkata",
  "extraction_mode": "promo_codes"
}
```

## PromoCode Model

The `PromoCode` model has the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | Yes | The actual promo code (e.g., "SAVE20") |
| `description` | string | No | What the code offers (e.g., "20% off") |
| `published_date_iso` | string | Yes | Date in YYYY-MM-DD format |
| `expiry_date` | string | No | When the code expires |
| `source_url` | string | No | Where the code came from |
| `category` | string | No | Type of code (discount, bonus, etc.) |

## WordPress Display

Promo codes are displayed in a styled section on your WordPress post:

```
┌─────────────────────────────────────────────────┐
│  🎁 Promo Codes for 31 January 2026             │
├─────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐   │
│  │ FREESPINS100  - Get 100 free spins       │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │ BONUS50  - 50% deposit bonus             │   │
│  └──────────────────────────────────────────┘   │
│                                                 │
│  Last updated: 2026-01-31 12:00:00 UTC         │
└─────────────────────────────────────────────────┘
```

The section uses WordPress Gutenberg blocks for proper formatting.

## Deduplication

Promo codes are deduplicated using a fingerprint system similar to links:

- Fingerprint format: `{CODE}|||{DATE}`
- Codes are case-insensitive (normalized to uppercase)
- Each site maintains its own fingerprint database

## API Endpoints

### Trigger Update (with promo codes)

```bash
curl -X POST http://localhost:8000/api/batch-update \
  -H 'Content-Type: application/json' \
  -d '{
    "post_ids": [105],
    "target_sites": ["all"]
  }'
```

### Manual Promo Code Addition

A new endpoint for manually adding promo codes:

```bash
curl -X POST http://localhost:8000/api/manual-promo-codes \
  -H 'Content-Type: application/json' \
  -d '{
    "post_id": 105,
    "codes": [
      {"code": "FREESPINS100", "description": "100 free spins bonus"},
      {"code": "BONUS50", "description": "50% deposit match"}
    ],
    "date": "2026-01-31",
    "target_sites": ["all"]
  }'
```

## Common Patterns for Extracting Promo Codes

### Pattern 1: Code in `<code>` tags

```html
<div class="promo-container">
  <code>BONUS123</code>
  <p>Get 100 free spins!</p>
</div>
```

```python
for code in soup.find_all('code'):
    codes.append(PromoCode(code=code.get_text(strip=True), ...))
```

### Pattern 2: Data attributes

```html
<button data-code="SAVE20" data-description="20% off">Copy Code</button>
```

```python
for btn in soup.find_all(attrs={"data-code": True}):
    code = btn.get("data-code")
    desc = btn.get("data-description")
```

### Pattern 3: Text patterns

```html
<p>Use code: FREEGAME to get bonus rewards!</p>
```

```python
pattern = re.compile(r'code[:\s]+([A-Z0-9]+)', re.IGNORECASE)
for match in pattern.findall(html):
    codes.append(PromoCode(code=match, ...))
```

### Pattern 4: Structured data (JSON-LD)

```html
<script type="application/ld+json">
{
  "@type": "Offer",
  "priceSpecification": {
    "priceCurrency": "USD",
    "price": "0"
  },
  "offeredBy": {"name": "GameSite"},
  "name": "Free Spins Bonus",
  "description": "Use code SPIN100",
  "validThrough": "2026-02-28"
}
</script>
```

```python
import json
for script in soup.find_all('script', type='application/ld+json'):
    data = json.loads(script.string)
    # Parse structured data for codes
```

## Migration Guide

### Existing Posts

Existing posts configured for link extraction will continue to work unchanged. The `extraction_mode` defaults to `"links"` for backward compatibility.

### Enabling Promo Codes

1. Create or update an extractor to implement `supports_promo_codes()` and `extract_promo_codes()`
2. Update the post configuration to set `extraction_mode` to `"promo_codes"` or `"both"`
3. Trigger an update to start extracting promo codes

## Troubleshooting

### No promo codes extracted

1. Check if the extractor's `supports_promo_codes()` returns `True`
2. Verify the HTML structure matches your extraction patterns
3. Check the logs for extraction details:
   ```
   [BATCH] Post 105 extraction_mode: promo_codes
   [BATCH] Extracted 0 promo codes using MySiteExtractor
   ```

### Duplicate codes appearing

- Ensure fingerprints are being saved correctly
- Check MongoDB `fingerprints` collection for `type: "promo_code"` entries

### Codes not appearing on WordPress

1. Verify the post content contains the SmartLink section anchor
2. Check if `extraction_mode` is properly configured
3. Review WordPress update logs for errors
