# Manual Link Addition Feature

## Overview
This feature allows users to manually add links to any configured post directly from the WordPress plugin interface. Manual links are treated exactly like automatically extracted links, with full deduplication and proper organization.

## User Workflow

### 1. Access the Feature
- Navigate to SmartLink Updater Dashboard
- Click the three-dot menu (⋮) next to any post
- Select "Add Links Manually"

### 2. Add Links
- **Date Selection**: Choose which date these links should be organized under (defaults to today)
- **Link Fields**: 
  - Each link has two fields: Title and URL
  - Start with 1 link field
  - Click "+ Add Another" to add more link fields
  - Click trash icon to remove a link field (must have at least 1)
- **Validation**: URLs are validated before submission

### 3. Submit
- Click "Add Links" button
- System will:
  - Validate all fields
  - Check for duplicates against existing links
  - Update the WordPress post
  - Store fingerprints for future deduplication
  - Show success message with duplicate count

## Technical Implementation

### Backend API

**Endpoint**: `POST /api/manual-links`

**Request Body**:
```json
{
  "post_id": 105,
  "links": [
    {
      "title": "Free Spins Link 1",
      "url": "https://example.com/link1"
    },
    {
      "title": "Free Spins Link 2",
      "url": "https://example.com/link2"
    }
  ],
  "date": "2025-11-10",
  "target": "this"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully added 2 manual links",
  "links_provided": 3,
  "links_added": 2,
  "duplicates": 1,
  "sections_pruned": 0
}
```

### Features

1. **Deduplication**
   - Checks against existing fingerprints for the post+date+site combination
   - Uses the same fingerprinting system as automatic extraction
   - Prevents duplicate links from being added

2. **Multi-site Support**
   - Works with multi-site configurations
   - Resolves correct post IDs for each site
   - Stores fingerprints per site

3. **Date Organization**
   - Links are organized under date headings in format "10 November 2025"
   - Date is customizable via date picker
   - Follows same date formatting as automatic extraction

4. **WordPress Integration**
   - Updates posts using the same `update_post_links_section` function
   - Maintains consistent HTML structure
   - Prunes old sections (5+ days old)

5. **Error Handling**
   - Validates URLs before submission
   - Shows clear error messages
   - Prevents submission if fields are empty or invalid

## UI Components

### Modal Design
- Clean, modern interface with Tailwind-inspired styling
- Responsive layout
- Clear visual hierarchy
- Intuitive controls

### Form Fields
- Title input (text)
- URL input (with validation)
- Date picker (defaults to today)
- Dynamic add/remove buttons

### Feedback
- Loading spinner during submission
- Success toast with duplicate count
- Error toasts for validation issues
- Table refresh after successful addition

## Use Cases

1. **Manual Link Discovery**: When users find links that automated extraction misses
2. **Backup/Historical Links**: Adding links from past dates
3. **Emergency Updates**: Quick link additions without waiting for scheduled updates
4. **Testing**: Verifying link format and post structure
5. **Migration**: Importing links from other sources

## Git Branch
Feature developed in: `feature/manual-link-addition`

## Files Modified
1. `backend/app/main.py` - Added API endpoint
2. `wordpress-plugin/smartlink-updater.php` - Added UI and client-side logic

## Testing Checklist
- [ ] Open manual links modal
- [ ] Add single link
- [ ] Add multiple links (3-5)
- [ ] Remove link fields
- [ ] Change date
- [ ] Submit with empty fields (should show error)
- [ ] Submit with invalid URL (should show error)
- [ ] Submit valid links
- [ ] Verify links appear in WordPress post
- [ ] Try adding duplicate links (should skip)
- [ ] Test with different post IDs
- [ ] Test with multi-site setup

## Future Enhancements
- Bulk import from CSV/JSON
- Link preview before submission
- Edit existing manual links
- Mark links as "manual" vs "auto" in database
- Analytics for manual vs automatic links
