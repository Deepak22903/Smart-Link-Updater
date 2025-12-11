# Custom Button Title Feature

## Overview
This feature allows you to manually set a button title for all buttons in a post, instead of using the titles scraped from target sites. You can toggle between custom titles and default (scraped) titles on a per-post basis.

## How It Works

### Backend Changes

1. **Data Models** (`backend/app/models.py` and `backend/app/mongo_models.py`):
   - Added `custom_button_title` (Optional[str]): Stores the custom button title text
   - Added `use_custom_button_title` (bool): Toggle flag to enable/disable custom titles

2. **WordPress Integration** (`backend/app/wp.py`):
   - Modified link generation logic to check `use_custom_button_title` flag
   - When enabled and `custom_button_title` is set, uses the custom title for ALL button links
   - When disabled, uses the original scraped title from the target site

3. **API Endpoints**:
   - Existing `/config/post/{post_id}` (PUT) endpoint automatically handles the new fields
   - No new endpoints needed - the fields are part of the `PostConfigUpdate` model

4. **MongoDB Storage**:
   - Fields are automatically persisted to MongoDB via existing `set_post_config()` function
   - No schema changes needed - MongoDB is schema-less

### Frontend Changes

1. **WordPress Plugin UI** (`wordpress-plugin/smartlink-updater.php`):
   - Added toggle switch in Post Configuration modal
   - Added text input for custom button title (shown when toggle is enabled)
   - Added CSS for modern toggle switch styling
   - Added JavaScript event handlers for toggle behavior

## Usage Instructions

### Setting Custom Button Title

1. Go to **SmartLink → Dashboard** in WordPress admin
2. Click **Edit Configuration** for any post
3. Scroll to the **Custom Button Title** section
4. Enable the toggle switch **"Use Custom Button Title"**
5. Enter your desired button title (e.g., "Claim Now", "Get Bonus", "Visit Site")
6. Click **Save Configuration**

### Reverting to Default Titles

1. Edit the post configuration
2. Toggle OFF **"Use Custom Button Title"**
3. Save the configuration
4. The system will use scraped titles from target sites

## Configuration Format

### JSON Example (posts.json or MongoDB):
```json
{
  "post_id": 105,
  "content_slug": "coin-master-free-spins",
  "source_urls": ["https://example.com/links/"],
  "timezone": "Asia/Kolkata",
  "use_custom_button_title": true,
  "custom_button_title": "Claim Now",
  "days_to_keep": 5
}
```

## Technical Details

### WordPress Plugin Flow:
1. User toggles the switch → `$('#use-custom-button-title').on('change')` event fires
2. Shows/hides the custom title input field
3. On save → `savePostConfig()` collects the values and sends to API
4. On edit → `openEditConfigModal()` loads saved values and sets the toggle state

### Backend Processing Flow:
1. API receives configuration with `use_custom_button_title` and `custom_button_title`
2. Saved to MongoDB via `mongo_storage.set_post_config()`
3. When updating WordPress post → `update_post_links_section()` in `wp.py`:
   - Checks `post_config.get('use_custom_button_title', False)`
   - If enabled, uses `post_config.get('custom_button_title')` for all link titles
   - If disabled, uses `link.title` (scraped from source)

## Default Behavior

- **Default**: `use_custom_button_title = False` (uses scraped titles)
- **When enabled without custom title**: Falls back to scraped titles
- **Scope**: Applies to ALL buttons in the post's daily link sections

## UI Elements

### Toggle Switch:
- Modern styled switch with smooth transition
- Blue background when enabled (#2271b1)
- Gray background when disabled (#ccc)

### Text Input:
- Only visible when toggle is enabled
- Placeholder text: "e.g., Claim Now, Get Bonus, Visit Site"
- Full-width input with modern styling

## Benefits

1. **Consistency**: All buttons in a post have the same title
2. **Branding**: Use your own call-to-action text instead of scraped titles
3. **Flexibility**: Toggle on/off per post without losing configuration
4. **User-Friendly**: Simple toggle switch - no complex configuration

## Example Use Cases

1. **Affiliate Sites**: Use "Claim Bonus" for all casino/gaming links
2. **Coupon Sites**: Use "Get Deal" for all coupon links  
3. **Review Sites**: Use "Visit Site" for all product links
4. **Multi-Language**: Use localized button text instead of English scraped titles

## Backward Compatibility

- Existing posts without the fields will default to `use_custom_button_title = False`
- No migration needed - the system gracefully handles missing fields
- Old configuration files work without changes
