# Button Styles System Guide

## Overview

The SmartLink Updater now supports **site-specific button designs**. Each WordPress site can have its own unique button style, allowing you to maintain brand consistency across different websites.

## Features

- ✅ **8 Pre-built Styles**: Choose from professionally designed button templates
- ✅ **Site-Specific**: Different button designs for each WordPress site
- ✅ **Live Preview**: See how buttons look before applying
- ✅ **MongoDB Storage**: Button style preferences persist across container restarts
- ✅ **Easy Configuration**: Simple dropdown selection in WordPress admin
- ✅ **Modular Architecture**: Easy to add new custom styles

## Available Button Styles

### 1. Default Pink Border
- **Style Key**: `default`
- **Description**: Pink border with white background, blue hover effect
- **Best For**: General purpose, playful brands
- **Colors**: Pink (#ff216d), Blue hover (#42a2f6)

### 2. Gradient Blue
- **Style Key**: `gradient_blue`
- **Description**: Blue-purple gradient background with white text
- **Best For**: Modern, tech-focused sites
- **Colors**: Purple to violet gradient with glow effect

### 3. Solid Green
- **Style Key**: `solid_green`
- **Description**: Solid green background with white text
- **Best For**: Call-to-action buttons, success themes
- **Colors**: Green (#10b981)

### 4. Orange Outline
- **Style Key**: `outline_orange`
- **Description**: Orange border outline with fill on hover
- **Best For**: Energy, enthusiasm, gaming sites
- **Colors**: Orange (#f97316)

### 5. Sunset Gradient
- **Style Key**: `gradient_sunset`
- **Description**: Warm sunset gradient from orange to pink
- **Best For**: Creative, lifestyle, and entertainment brands
- **Colors**: Pink to coral gradient with shadow

### 6. Modern Dark
- **Style Key**: `modern_dark`
- **Description**: Dark background with subtle border
- **Best For**: Premium, sophisticated brands
- **Colors**: Dark gray (#1f2937)

### 7. Neon Purple
- **Style Key**: `neon_purple`
- **Description**: Vibrant purple with neon glow effect
- **Best For**: Gaming, nightlife, trendy brands
- **Colors**: Purple (#7c3aed) with neon glow

### 8. Minimal Blue
- **Style Key**: `minimal_blue`
- **Description**: Clean minimal design with subtle blue
- **Best For**: Professional, corporate sites
- **Colors**: Light blue background with dark blue text

## How to Configure

### Via WordPress Admin (Recommended)

1. **Navigate to SmartLink Updater → Sites**
2. **Add or Edit a Site**
3. **Select Button Design Style** from the dropdown
4. **Preview** the button style (optional)
5. **Save** the site configuration

### Via API

**Endpoint**: `PUT /api/sites/{site_key}`

```json
{
  "site_key": "mysite",
  "base_url": "https://example.com",
  "username": "admin@example.com",
  "app_password": "xxxx xxxx xxxx xxxx",
  "button_style": "gradient_blue"
}
```

## Architecture

### Backend Components

#### 1. `backend/app/button_styles.py`
- **Purpose**: Button style templates and HTML generation
- **Key Functions**:
  - `get_button_style(style_name)` - Retrieve style configuration
  - `get_all_button_styles()` - List all available styles
  - `generate_button_html(link, style_name)` - Generate WordPress block HTML

#### 2. `backend/app/mongo_storage.py`
- **Purpose**: Persist button_style in wp_sites collection
- **Field**: `button_style` (string, default: "default")

#### 3. `backend/app/wp.py`
- **Purpose**: Apply button styles when updating WordPress posts
- **Key Logic**:
  - Extracts `button_style` from `wp_site` configuration
  - Passes style to `button_styles.generate_button_html()`
  - Generates site-specific button HTML

#### 4. `backend/app/main.py`
- **Purpose**: API endpoints for button styles
- **Endpoints**:
  - `GET /api/button-styles` - List all available styles
  - `GET /api/button-styles/{style_name}` - Get specific style details
  - `GET /api/button-styles/preview/{style_name}` - Generate preview HTML

### Frontend Components

#### 1. WordPress Plugin UI
- **Location**: Sites Management page
- **Features**:
  - Dropdown selector with all 8 styles
  - Live button preview
  - Persistent storage in MongoDB

#### 2. Button Style Preview
- **How It Works**:
  - User selects style from dropdown
  - AJAX call to `/api/button-styles/preview/{style}`
  - Preview rendered in modal with sample button

## Adding Custom Button Styles

### Step 1: Define Style in `button_styles.py`

```python
BUTTON_STYLES = {
    # ... existing styles ...
    
    "custom_style": {
        "name": "My Custom Style",
        "description": "Description of the style",
        "css": {
            "padding": "15px 30px",
            "border": "2px solid #000",
            "border-radius": "8px",
            "background-color": "#fff",
            "color": "#000",
            "font-size": "18px",
            "font-weight": "bold",
            # ... more CSS properties
        },
        "hover": {
            "background-color": "#000",
            "color": "#fff"
        }
    }
}
```

### Step 2: Update WordPress Plugin Dropdown

In `wordpress-plugin/smartlink-updater.php`, add option:

```html
<select id="site-button-style" class="smartlink-input">
    <!-- ... existing options ... -->
    <option value="custom_style">My Custom Style</option>
</select>
```

### Step 3: Update Display Name Mapping

In the sites table rendering JavaScript:

```javascript
const styleNames = {
    // ... existing styles ...
    'custom_style': 'My Custom Style'
};
```

## API Reference

### Get All Button Styles

```bash
GET /api/button-styles
```

**Response**:
```json
{
  "styles": {
    "default": {
      "name": "Default Pink Border",
      "description": "Pink border with white background",
      "css": { ... },
      "hover": { ... }
    },
    // ... more styles
  }
}
```

### Get Specific Style

```bash
GET /api/button-styles/gradient_blue
```

**Response**:
```json
{
  "style_name": "gradient_blue",
  "style": {
    "name": "Gradient Blue",
    "description": "Blue gradient background",
    "css": { ... },
    "hover": { ... }
  }
}
```

### Preview Style

```bash
GET /api/button-styles/preview/gradient_blue
```

**Response**:
```json
{
  "style_name": "gradient_blue",
  "html": "<!-- wp:column ... -->"
}
```

## Database Schema

### wp_sites Collection

```json
{
  "_id": ObjectId("..."),
  "site_key": "mysite",
  "base_url": "https://example.com",
  "username": "admin@example.com",
  "app_password": "xxxx xxxx xxxx",
  "button_style": "gradient_blue",
  "display_name": "My Site",
  "created_at": "2025-12-03T10:00:00",
  "updated_at": "2025-12-03T10:00:00"
}
```

## Best Practices

### 1. Button Style Selection

- **Match brand colors**: Choose styles that align with site branding
- **Consider contrast**: Ensure buttons stand out from background
- **Test on mobile**: Preview how buttons look on different devices
- **User experience**: Pick styles that clearly indicate clickability

### 2. Custom Styles

- **Use web-safe colors**: Ensure colors work across browsers
- **Accessibility**: Maintain WCAG contrast ratios (minimum 4.5:1)
- **Responsive design**: Test button padding on mobile screens
- **Performance**: Avoid heavy animations that impact load time

### 3. Maintenance

- **Document custom styles**: Add comments explaining design choices
- **Version control**: Track style changes in git
- **Testing**: Test buttons in WordPress editor and live site
- **Consistency**: Use similar styles across related sites

## Troubleshooting

### Buttons Not Updating

**Problem**: Button style not applied after changing configuration

**Solutions**:
1. Verify site configuration saved correctly in MongoDB
2. Check logs for button_style value: `[WP] Site button style: {style}`
3. Trigger a manual update to regenerate post content
4. Clear WordPress cache if using caching plugins

### Preview Not Showing

**Problem**: Button preview doesn't load in modal

**Solutions**:
1. Check API endpoint is accessible: `/api/button-styles/preview/{style}`
2. Verify CORS settings allow requests from WordPress site
3. Check browser console for JavaScript errors
4. Ensure button_styles.py is imported correctly

### Custom Style Not Working

**Problem**: Custom button style not rendering correctly

**Solutions**:
1. Validate CSS properties in `button_styles.py`
2. Check JavaScript property conversion (e.g., `border-color` → `borderColor`)
3. Test style preview API endpoint directly
4. Verify style name matches in all locations (Python, PHP, JS)

## Migration Guide

### Existing Sites Without Button Style

All existing sites will automatically default to `"default"` style (pink border). To change:

1. Edit site in WordPress admin
2. Select desired button style
3. Save configuration
4. Trigger update on affected posts

### Bulk Update Script

To update all sites to a specific style:

```python
from backend.app import mongo_storage

sites = mongo_storage.get_all_wp_sites()
for site_key, site_data in sites.items():
    site_data['button_style'] = 'gradient_blue'
    mongo_storage.set_wp_site(site_key, site_data)
```

## Performance Considerations

- **No Runtime Overhead**: Button HTML generated once during post update
- **Cached in WordPress**: Button styles embedded in post content
- **No External CSS**: All styles inline, no additional HTTP requests
- **Minimal JS**: Only used for admin preview, not on live site

## Future Enhancements

Potential improvements to consider:

1. **Style Editor**: Visual editor for creating custom styles
2. **Style Import/Export**: Share button styles between installations
3. **A/B Testing**: Test different button styles for conversion
4. **Animation Library**: Add animated hover effects
5. **Button Templates**: Pre-configured sets of styles per industry
6. **Color Picker**: Allow custom color selection per style
7. **Font Customization**: Custom fonts for button text

## Support

For issues or questions about button styles:

1. Check logs: `[WP] Site button style: ...`
2. Verify MongoDB: `db.wp_sites.find({"site_key": "mysite"})`
3. Test API: `curl http://localhost:8000/api/button-styles`
4. Review `button_styles.py` for style definitions
