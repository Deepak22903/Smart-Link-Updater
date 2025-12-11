# Custom Button Title Feature - UI Guide

## WordPress Admin Interface

### Location
Navigate to: **SmartLink → Dashboard → Edit Configuration (for any post)**

### UI Components

```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 Custom Button Title (Optional)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ℹ️ Override the button title for all links. When disabled,        │
│     uses the title from the target site.                            │
│                                                                      │
│  ┌─────┐                                                            │
│  │ ◯   │  Use Custom Button Title                                   │
│  └─────┘                                                            │
│  ↑                                                                   │
│  Toggle Switch (OFF by default)                                     │
│                                                                      │
│  [When Toggle is ON, shows:]                                        │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Claim Now, Get Bonus, Visit Site                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ↑                                                                   │
│  Text Input (placeholder text)                                      │
│                                                                      │
│  This title will be used for all buttons instead of the            │
│  scraped titles from target sites.                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Toggle Switch States

### OFF (Default) - Uses Scraped Titles
```
┌─────┐
│ ◯   │  Use Custom Button Title
└─────┘
Gray background, circle on left
```

**Result**: Each button shows its unique scraped title
- Button 1: "Get 50 Free Spins - Site1"
- Button 2: "Claim Your Bonus - Site2"
- Button 3: "Free Spins Here - Site3"

### ON - Uses Custom Title
```
┌─────┐
│   ◯ │  Use Custom Button Title
└─────┘
Blue background (#2271b1), circle on right
```

**Shows text input field:**
```
┌──────────────────────────────────────────────────────────────┐
│ Claim Free Spins Now                                          │
└──────────────────────────────────────────────────────────────┘
```

**Result**: All buttons show the same custom title
- Button 1: "Claim Free Spins Now"
- Button 2: "Claim Free Spins Now"
- Button 3: "Claim Free Spins Now"

## Complete Configuration Example

### Post Configuration Modal View

```
┌─────────────────────────────────────────────────────────────────┐
│ Edit Post Configuration                                   [X]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Content Slug                                                     │
│ ┌──────────────────────────────────────┐                       │
│ │ coin-master-free-spins                │                       │
│ └──────────────────────────────────────┘                       │
│                                                                  │
│ Source URLs                                                      │
│ ┌──────────────────────────────────────┐                       │
│ │ https://example.com/links/            │ [X]                   │
│ └──────────────────────────────────────┘                       │
│ [+ Add Another URL]                                             │
│                                                                  │
│ Timezone                                                         │
│ ┌──────────────────────────────────────┐                       │
│ │ Asia/Kolkata (IST)                   ▼│                       │
│ └──────────────────────────────────────┘                       │
│                                                                  │
│ Days to Keep Sections                                           │
│ ┌──────────────────────────────────────┐                       │
│ │ 5                                     │                       │
│ └──────────────────────────────────────┘                       │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 🔘 Custom Button Title (Optional)                        │   │
│ │                                                           │   │
│ │ ℹ️ Override the button title for all links              │   │
│ │                                                           │   │
│ │ ┌─────┐                                                  │   │
│ │ │   ◯ │ Use Custom Button Title                         │   │
│ │ └─────┘                                                  │   │
│ │                                                           │   │
│ │ ┌───────────────────────────────────────────────────┐   │   │
│ │ │ Claim Free Spins Now                               │   │   │
│ │ └───────────────────────────────────────────────────┘   │   │
│ │                                                           │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                   [Cancel] [✓ Save Configuration]│
└─────────────────────────────────────────────────────────────────┘
```

## CSS Styling Details

### Toggle Switch
- **Width**: 60px
- **Height**: 28px
- **Border Radius**: 28px (fully rounded)
- **Colors**:
  - OFF: #ccc (light gray)
  - ON: #2271b1 (WordPress blue)
- **Circle Size**: 20px × 20px
- **Transition**: 0.4s smooth animation

### Text Input
- **Width**: 100%
- **Padding**: 12px
- **Border**: 2px solid #ddd
- **Border Radius**: 8px
- **Font Size**: 14px

## User Flow

1. **Initial State**: Toggle is OFF, text input is hidden
2. **Click Toggle**: 
   - Toggle switches to ON (blue)
   - Text input fades in
3. **Type Custom Title**: User enters desired button text
4. **Click Save**: Configuration is saved to database
5. **Next Update**: All new buttons will use the custom title

## API Request Example

### When Saving Configuration

```javascript
{
  "post_id": 105,
  "content_slug": "coin-master-free-spins",
  "source_urls": ["https://example.com/links/"],
  "timezone": "Asia/Kolkata",
  "days_to_keep": 5,
  "use_custom_button_title": true,
  "custom_button_title": "Claim Free Spins Now"
}
```

### When Loading Configuration

The same fields are returned by GET `/config/post/105` and populate the form fields.

## Keyboard Shortcuts

- **Tab**: Navigate between form fields
- **Space**: Toggle the switch (when focused)
- **Enter**: Submit the form (save configuration)

## Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (responsive design)

## Accessibility

- Toggle has proper `<label>` association
- Text input has placeholder for guidance
- Sufficient color contrast for visibility
- Keyboard navigable
- Screen reader friendly
