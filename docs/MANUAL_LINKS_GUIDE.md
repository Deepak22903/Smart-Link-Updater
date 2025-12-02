# Manual Link Addition - Quick Start Guide

## Feature Overview

Add links manually to any post with a beautiful, intuitive interface. All manual links are deduplicated and organized just like automatically extracted links.

## How to Use

### Step 1: Open the Menu
Click the three-dot menu (⋮) next to any post and select **"Add Links Manually"**

```
┌─────────────────────────────────────┐
│ Post: Coin Master Free Spins        │
│ ⋮ Action Menu                       │
│   ├─ 📄 View Logs                   │
│   ├─ ➕ Add Links Manually  ← Click │
│   ├─ ✏️  Edit                       │
│   └─ 🗑️  Delete                     │
└─────────────────────────────────────┘
```

### Step 2: Fill in the Form

```
┌──────────────────────────────────────────────────┐
│  ➕ Add Links Manually                      ✕    │
├──────────────────────────────────────────────────┤
│                                                  │
│  📌 Post: Coin Master Free Spins                │
│     Add links that will be inserted into this    │
│     post. Duplicates will be automatically       │
│     filtered.                                    │
│                                                  │
│  Date for Links                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ 2025-11-10                               │   │
│  └──────────────────────────────────────────┘   │
│  Links will be organized under this date heading│
│                                                  │
│  Links                            [➕ Add Another]│
│  ┌──────────────────────────────────────────┐   │
│  │ LINK 1                              🗑️   │   │
│  │ Title *                                   │   │
│  │ ┌────────────────────────────────────┐   │   │
│  │ │ Free Spins Link 1                  │   │   │
│  │ └────────────────────────────────────┘   │   │
│  │ URL *                                     │   │
│  │ ┌────────────────────────────────────┐   │   │
│  │ │ https://example.com/link1          │   │   │
│  │ └────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │ LINK 2                              🗑️   │   │
│  │ Title *                                   │   │
│  │ ┌────────────────────────────────────┐   │   │
│  │ │ Free Spins Link 2                  │   │   │
│  │ └────────────────────────────────────┘   │   │
│  │ URL *                                     │   │
│  │ ┌────────────────────────────────────┐   │   │
│  │ │ https://example.com/link2          │   │   │
│  │ └────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
├──────────────────────────────────────────────────┤
│                         [Cancel] [✓ Add Links]   │
└──────────────────────────────────────────────────┘
```

### Step 3: Success!

After submission, you'll see:

```
✓ Successfully added 2 manual links
  (1 duplicate skipped)
```

The links will be added to your WordPress post under the selected date heading.

## Key Features

### ✨ Dynamic Fields
- Start with 1 link field
- Click "+ Add Another" for more fields
- Remove unwanted fields (minimum 1 required)

### 🔍 Smart Deduplication
- Automatically checks against existing links
- Same fingerprinting as automated extraction
- Shows duplicate count after submission

### 📅 Date Organization
- Choose any date for your links
- Links organized under formatted heading (e.g., "10 November 2025")
- Defaults to today's date

### ✅ Validation
- URL format validation
- Required field checking
- Clear error messages
- Visual feedback (red borders for errors)

### 🎯 Multi-site Support
- Works with multi-site configurations
- Resolves correct post IDs automatically
- Stores fingerprints per site

## API Usage

For programmatic access:

```bash
curl -X POST http://your-backend/api/manual-links \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 105,
    "links": [
      {"title": "Link 1", "url": "https://example.com/1"},
      {"title": "Link 2", "url": "https://example.com/2"}
    ],
    "date": "2025-11-10",
    "target": "this"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Successfully added 2 manual links",
  "links_provided": 2,
  "links_added": 2,
  "duplicates": 0
}
```

## Tips & Best Practices

1. **Date Selection**: Use past dates to add historical links or future dates for scheduled content
2. **Title Format**: Use clear, descriptive titles that match your site's style
3. **URL Validation**: The system validates URLs, but double-check they're correct
4. **Bulk Addition**: Add multiple links at once - they'll all be processed together
5. **Duplicate Check**: Don't worry about duplicates - they're automatically filtered

## Troubleshooting

### "Post not configured"
- Make sure the post has been configured with source URLs and WordPress site settings first

### "Invalid URL format"
- URLs must start with http:// or https://
- Check for typos or missing protocol

### "Failed to add links"
- Check backend connection
- Verify post ID is correct
- Check browser console for detailed errors

## Development

Feature branch: `feature/manual-link-addition`

To merge to main:
```bash
git checkout main
git merge feature/manual-link-addition
```

## Related Documentation

- See `MANUAL_LINKS_FEATURE.md` for technical details
- See `FEATURE_DOCUMENTATION.md` for all features
