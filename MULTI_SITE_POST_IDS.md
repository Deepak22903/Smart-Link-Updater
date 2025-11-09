# Multi-Site Post ID Mapping Guide

## The Problem

When you have the same article on multiple WordPress sites, each site assigns a **different post ID** to that article:

- Site A (minecraftcirclegenerater.com): "Coin Master Free Spins" = Post ID **105**
- Site B (casino-tips.com): "Coin Master Free Spins" = Post ID **89**  
- Site C (gaming-blog.com): "Coin Master Free Spins" = Post ID **234**

The old system only stored one `post_id`, so updating "all sites" would try to update post ID 105 on every site, which would fail for Site B and Site C.

## The Solution

The system now supports **content slugs** and **site-specific post ID mappings**:

```json
{
  "content_slug": "coin-master-free-spins",
  "post_id": 105,
  "site_post_ids": {
    "this": 105,
    "minecraft": 105,
    "casino": 89,
    "gaming_blog": 234
  }
}
```

When you select "Update All Sites", the system:
1. Extracts links once from source URLs
2. For each site, uses the correct post ID from `site_post_ids`
3. Updates each site with the resolved post ID

## How to Configure

### Option 1: Add via WordPress Dashboard (Coming Soon)

The "Add New Config" and "Edit" forms will include fields for:
- Content Slug (e.g., "coin-master-free-spins")
- Post IDs for each configured site

### Option 2: Add via API (Current Method)

```bash
curl -X POST https://smartlink-api-601738079869.us-central1.run.app/config/post \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 105,
    "content_slug": "coin-master-free-spins",
    "site_post_ids": {
      "this": 105,
      "minecraft": 105,
      "casino": 89,
      "gaming_blog": 234
    },
    "source_urls": [
      "https://simplegameguide.com/coin-master-free-spins/"
    ],
    "timezone": "Asia/Kolkata"
  }'
```

### Option 3: Add via MongoDB (Direct)

Connect to your MongoDB Atlas and update the `posts` collection:

```javascript
db.posts.updateOne(
  { post_id: 105 },
  { 
    $set: {
      content_slug: "coin-master-free-spins",
      site_post_ids: {
        this: 105,
        minecraft: 105,
        casino: 89,
        gaming_blog: 234
      }
    }
  }
)
```

## Content Slug Naming Convention

Choose descriptive, URL-friendly slugs:

✅ **Good Examples:**
- `coin-master-free-spins`
- `minecraft-circle-generator`
- `roblox-promo-codes`
- `travel-town-energy`

❌ **Bad Examples:**
- `post1` (not descriptive)
- `Coin Master Free Spins!` (has spaces and special characters)
- `105` (just a number, not semantic)

## Finding Post IDs on Each Site

To find the post ID on each WordPress site:

### Method 1: WordPress Admin
1. Log into the WordPress site
2. Go to **Posts → All Posts**
3. Hover over the post title
4. Look at the URL in browser status bar: `...post.php?post=105&action=edit`
5. The number after `post=` is the post ID (105)

### Method 2: REST API
```bash
# Find post by slug
curl https://your-site.com/wp-json/wp/v2/posts?slug=coin-master-free-spins

# Returns: [{"id": 89, "title": "Coin Master Free Spins", ...}]
```

### Method 3: Database Query
```sql
SELECT ID, post_title, post_name 
FROM wp_posts 
WHERE post_name = 'coin-master-free-spins' 
AND post_status = 'publish';
```

## Migration Guide

### Migrating Existing Configurations

If you have existing posts configured with only `post_id`, you need to add the multi-site mapping:

**Step 1: List all your configured posts**
```bash
curl https://smartlink-api-601738079869.us-central1.run.app/api/posts/list
```

**Step 2: For each post, gather post IDs from all sites**

Create a mapping spreadsheet:

| Content Slug | This Site | minecraft | casino | gaming_blog |
|--------------|-----------|-----------|--------|-------------|
| coin-master-free-spins | 105 | 105 | 89 | 234 |
| minecraft-circles | 111 | 111 | 92 | 240 |

**Step 3: Update each post configuration**

```bash
# Update post 105
curl -X PUT https://smartlink-api-601738079869.us-central1.run.app/config/post/105 \
  -H "Content-Type: application/json" \
  -d '{
    "content_slug": "coin-master-free-spins",
    "site_post_ids": {
      "this": 105,
      "minecraft": 105,
      "casino": 89,
      "gaming_blog": 234
    }
  }'
```

**Step 4: Test with a single post**

1. Select a post in WordPress dashboard
2. Choose "Update Target: All Sites"
3. Click Update
4. Verify all sites were updated correctly

## Backward Compatibility

The system maintains backward compatibility:

- **Old configs** (only `post_id`): Still work for "This Site" updates
- **New configs** (`content_slug` + `site_post_ids`): Work for all update targets
- **Mixed configs**: System falls back to `post_id` if site not in `site_post_ids`

## Troubleshooting

### "No post ID configured for site 'casino'"

**Cause**: The config has no entry in `site_post_ids` for that site.

**Fix**: Add the mapping:
```bash
curl -X PUT https://smartlink-api-601738079869.us-central1.run.app/config/post/105 \
  -H "Content-Type: application/json" \
  -d '{
    "site_post_ids": {
      "this": 105,
      "minecraft": 105,
      "casino": 89
    }
  }'
```

### Update fails for specific site

**Check:**
1. Does the post exist on that site? (Verify post ID)
2. Are the WordPress credentials correct for that site? (Check `WP_SITES` in env-config.yaml)
3. Is the site accessible? (Check site URL)

**Debug:**
```bash
# Test site credentials
curl -X GET https://your-site.com/wp-json/wp/v2/posts/89 \
  -u "username:application_password"
```

### Content slug conflicts

**Error**: "Duplicate key error on content_slug"

**Cause**: Another post already has that slug.

**Fix**: Choose a unique slug:
- Add site prefix: `minecraft-coin-master-free-spins`
- Add date: `coin-master-free-spins-2025`
- Add category: `casino-coin-master-free-spins`

## Best Practices

1. **Use Descriptive Slugs**: Make them human-readable and SEO-friendly
2. **Document Mappings**: Keep a spreadsheet of which post IDs map to which sites
3. **Test Before Bulk Updates**: Always test with one post before updating 50+ posts
4. **Consistent Slugs**: Use the same post slug across all WordPress sites when possible
5. **Version Control**: Keep your post mappings in a JSON file in your repo

## Example: Complete Multi-Site Configuration

```json
{
  "content_slug": "coin-master-free-spins-daily",
  "post_id": 105,
  "site_post_ids": {
    "this": 105,
    "minecraft": 105,
    "casino_main": 89,
    "casino_blog": 234,
    "gaming_news": 412
  },
  "source_urls": [
    "https://simplegameguide.com/coin-master-free-spins/",
    "https://techyhigher.com/coin-master-daily-links/"
  ],
  "extractor_map": {
    "https://simplegameguide.com/coin-master-free-spins/": "simplegameguide",
    "https://techyhigher.com/coin-master-daily-links/": "techyhigher"
  },
  "timezone": "Asia/Kolkata",
  "created_at": "2025-11-01T10:30:00Z",
  "updated_at": "2025-11-09T15:45:00Z",
  "last_updated": "2025-11-09T15:45:00Z"
}
```

This configuration:
- ✅ Works with 5 different WordPress sites
- ✅ Extracts from 2 source URLs with specific extractors
- ✅ Has a semantic content slug
- ✅ Tracks creation and update timestamps

## Future Enhancements

Coming soon:
- [ ] UI for managing site_post_ids in WordPress dashboard
- [ ] Auto-detection of matching posts across sites by slug
- [ ] Bulk import tool for migrating existing configs
- [ ] Visual mapping interface showing which posts map where
- [ ] Sync check to verify posts exist on all configured sites
