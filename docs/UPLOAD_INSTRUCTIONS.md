# How to Upload Updated Plugin to Server

## Quick Upload Steps

### Option 1: Using SCP (Recommended)
```bash
# From your local machine, run:
scp -P 65002 wordpress-plugin/smartlink-updater.php root@82.29.199.62:~/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/
```

### Option 2: Using SFTP Client
1. Connect to: `82.29.199.62:65002`
2. Navigate to: `~/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/`
3. Upload `smartlink-updater.php` (replace existing file)

### Option 3: Manual Copy-Paste
1. SSH into server: `ssh -p 65002 root@82.29.199.62`
2. Open file: `nano ~/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/smartlink-updater.php`
3. Copy content from local `wordpress-plugin/smartlink-updater.php`
4. Paste and save (Ctrl+O, Enter, Ctrl+X)

## After Upload

1. **Clear WordPress Cache** (if you have caching plugin)
2. **Hard Refresh Browser**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
3. Go to WordPress Admin → SmartLink Updater

## What You Should See

In the Actions column of each post row, you'll now see:
- **[Update]** button
- **[Logs]** button  
- **[⋮]** (three dots menu) ← **NEW!**

Click the three-dot menu to see:
- ✏️ Edit Config
- 🔄 View History
- ❤️ Reset Health
- 🗑️ Delete Config

## Features Added Since Last Upload

### ✅ Task #1: Post Title Display
- Shows actual WordPress post titles instead of just IDs
- Titles are clickable links to edit post in WordPress

### ✅ Task #2: Statistics Dashboard
- 4 gradient cards at top showing post counts by health status
- Real-time updates when posts change

### ✅ Task #3: Last Updated Column
- Shows relative time ("2 hours ago") for each post
- Updates when you refresh the posts list

### ✅ Task #4: Quick Actions Menu
- **Edit Config**: Opens modal to edit extractor, source URL, timezone
- **View History**: Shows update timeline (preview UI ready)
- **Reset Health**: Resets health status to "unknown"
- **Delete Config**: Removes post configuration with confirmation

## Troubleshooting

**If you don't see the three-dot menu after upload:**

1. **Clear browser cache**: 
   - Chrome/Edge: Ctrl+Shift+Delete → Clear cached images and files
   - Firefox: Ctrl+Shift+Delete → Cached Web Content

2. **Hard refresh the page**: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

3. **Check browser console**: F12 → Console tab → Look for JavaScript errors

4. **Verify file was uploaded**: SSH to server and check file size/date:
   ```bash
   ls -lh ~/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/smartlink-updater.php
   ```

5. **Check WordPress debug**: Add to wp-config.php:
   ```php
   define('WP_DEBUG', true);
   define('WP_DEBUG_LOG', true);
   ```

## File Location Reference

**Local:** `/home/deepak/data/SmartLinkUpdater/wordpress-plugin/smartlink-updater.php`

**Server:** `~/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/smartlink-updater.php`

**Server Full Path:** `/home/deepak/domains/minecraftcirclegenerater.com/public_html/wp-content/plugins/smart-link-updater/smartlink-updater.php`
