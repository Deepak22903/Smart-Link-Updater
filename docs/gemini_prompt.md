# Gemini Extraction Prompt Design

Use this prompt with Projects API or REST to ensure Gemini returns only links under sections like "Links for Today" or headings containing today's date.

## JSON schema

```json
{
  "type": "object",
  "properties": {
    "links": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "url": {"type": "string"},
          "title": {"type": "string"},
          "published_date_iso": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
          "section_heading": {"type": "string"},
          "summary": {"type": "string"}
        },
        "required": ["url", "title", "published_date_iso", "section_heading"]
      }
    },
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "extraction_notes": {"type": "string"}
  },
  "required": ["links", "confidence"]
}
```

## Prompt template

```
You are assisting with updating WordPress posts that list daily links. The HTML fragment provided was scraped from the source page.

Instructions:
1. Find sections where the heading contains "links for today" or today’s date ({{today_iso}}) in any common format (YYYY-MM-DD, DD Month YYYY, Month DD, YYYY).
2. Only extract anchor tags that appear under those sections.
3. Ignore duplicates (same href) and ignore links without an explicit text anchor.
4. For each link, provide the URL, anchor text as the title, the ISO date (YYYY-MM-DD) inferred from the section, and the section heading text you used.
5. Do not fabricate URLs or dates. If the section is missing, return an empty list.
6. Respond strictly with JSON following the provided schema. Do not add extra keys.

Context values:
- today_iso: {{today_iso}}
- canonical_timezone: {{timezone}}
```

## Validation guardrails

- Reject the response if `confidence < 0.5`.
- After receiving the JSON, re-check each link with regex to ensure they sit within the expected heading section (use BeautifulSoup fallback).
- Deduplicate using URL + date.
