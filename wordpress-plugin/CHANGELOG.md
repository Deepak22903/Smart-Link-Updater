# SmartLink Updater - WordPress Plugin Changelog

## Version 2.0.0 (2025-10-27)

### ✨ New Features
- **Multi-Site Support**: Display which posts target custom WordPress sites vs. the default site
- **Visual Indicators**: 
  - 🏠 Green home icon for posts updating on this site (default)
  - 🌐 Orange site icon for posts updating on custom WordPress sites
- **Target Site Column**: New column showing the destination WordPress site URL
- **Multi-Site Documentation**: Expandable help section explaining how to configure multi-site updates

### 🔧 Improvements
- Updated plugin description to mention multi-site, custom extractors, and Gemini AI capabilities
- Better visual organization of the admin dashboard
- Improved table layout for better readability

### 📖 Documentation
- Added inline help explaining multi-site configuration
- Links to `MULTISITE.md` for detailed setup instructions

### ⚙️ Technical Changes
- Plugin now reads `wp_site` configuration from API responses
- Gracefully handles both default and custom site configurations
- Version bumped to 2.0.0 to reflect major new feature

---

## Version 1.0.0 (Initial Release)

### Features
- One-click link updates from post editor
- Admin dashboard showing all configured posts
- Health check for API status
- Bulk update all posts functionality
- Real-time update results display
- Integration with Cloud Run API

