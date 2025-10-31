# SmartLink Updater - WordPress Plugin

A powerful WordPress plugin that automatically updates post links using a Cloud Run API backend with support for multiple sites, custom extractors, and AI-powered link extraction.

## Version 2.0.0 - Multi-Site Support

## 📦 Installation

1. **Download the plugin files:**
   - `smartlink-updater.php`
   - `smartlink-updater.js`

2. **Upload to WordPress:**
   ```
   wp-content/plugins/smartlink-updater/
   ├── smartlink-updater.php
   └── smartlink-updater.js
   ```

3. **Activate the plugin:**
   - Go to WordPress Admin → Plugins
   - Find "SmartLink Updater"
   - Click "Activate"

## 🎯 Usage

1. **Edit any post** (that's configured in your Cloud Run API)
2. Look for the **"SmartLink Updater"** meta box in the sidebar
3. Click the **"Update Links Now"** button
4. Wait for the update to complete
5. The page will automatically reload with updated links

## ✨ Features

### 🔄 One-Click Updates
- Update post links directly from the post editor
- Real-time progress feedback and statistics
- Automatic page reload after success
- Beautiful UI integrated with WordPress design

### 🌐 Multi-Site Support (NEW in v2.0)
- **Update posts on multiple WordPress sites** from a single installation
- Visual indicators show which site each post targets:
  - 🏠 **Default site** (this WordPress installation)
  - 🌐 **Custom site** (external WordPress installation)
- Configure different WordPress credentials per post
- Perfect for managing multiple gaming/news sites

### 📊 Admin Dashboard
- View all configured posts at once
- See source URLs and target sites
- Update individual posts or all posts together
- Monitor API health status in real-time

### 🤖 Intelligent Extraction
- **Custom Extractors**: Site-specific extractors (e.g., simplegameguide.com)
- **AI Fallback**: Gemini AI handles unknown site formats automatically
- **Two-Stage Processing**: Optimized for speed and accuracy

### 🔒 Security
- WordPress Application Passwords for authentication
- Secure API communication with nonce verification
- Multi-site credentials stored securely in backend

## 🔧 Configuration

The plugin is pre-configured to use your Cloud Run API:
```
https://smartlink-api-601738079869.us-central1.run.app
```

To change the API URL, edit line 20 in `smartlink-updater.php`:
```php
private $api_base_url = 'https://your-api-url.run.app';
```

## 📸 Screenshot

The meta box will appear in the post editor sidebar showing:
- Update button
- Status messages (success/error)
- Statistics (links found, links added, sections pruned)
- Date of update

## 🛠️ Troubleshooting

**Button doesn't work:**
- Check browser console for JavaScript errors
- Ensure jQuery is loaded on the page

**API request fails:**
- Verify the Cloud Run service is running
- Check that the post ID is configured in the API
- Review Cloud Run logs for errors

**Permission errors:**
- Ensure you have editor/administrator privileges
- Check that AJAX requests are allowed

## 🔐 Security

- Uses WordPress nonces for CSRF protection
- Validates post IDs before API calls
- Only accessible to logged-in users with editing permissions

## 📝 Version History

### 1.0.0 (2025-10-26)
- Initial release
- One-click link updates
- Real-time status feedback
- Integration with Cloud Run API

## 📞 Support

For issues or questions:
- Check Cloud Run logs: `gcloud run services logs read smartlink-api --region=us-central1`
- Test API directly: `curl -X POST https://smartlink-api-601738079869.us-central1.run.app/update-post/4166`

## 📄 License

GPL v2 or later
