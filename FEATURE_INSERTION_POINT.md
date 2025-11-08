# Custom Link Insertion Point Feature

## 🎯 Feature Overview
Added ability to insert the daily links section at a **specific location** in WordPress posts instead of always prepending to the beginning.

## 🔧 Implementation Details

### 1. Data Models Updated
- **`PostConfig`** and **`PostConfigUpdate`** in `main.py`
- **`PostConfig`** in `mongo_models.py`
- Added new field: `insertion_point: Optional[Dict[str, str]]`

### 2. Function Signature Updated
- **`update_post_links_section()`** in `wp.py`
- New parameter: `insertion_point: Optional[Dict[str, str]] = None`

### 3. Insertion Logic
Supports three modes:

#### Mode 1: Prepend (Default)
```python
{"type": "prepend"}
```
- Inserts at beginning of post content (current behavior)

#### Mode 2: After Heading ID
```python
{"type": "after_heading_id", "value": "Coin_Master_Free_Spins_Coins_Links"}
```
- Finds heading with matching `id` attribute or `ez-toc-data-id`
- Inserts links section immediately after that heading
- Falls back to prepend if heading not found

#### Mode 3: After Heading Text
```python
{"type": "after_heading_text", "value": "Coin Master Free Spins"}
```
- Finds heading containing the specified text
- Case-insensitive search
- Falls back to prepend if not found

### 4. Regex Patterns
```python
# For ID-based matching:
heading_pattern = rf'(<h[1-6][^>]*(?:id="{re.escape(insertion_value)}"|id=\'{re.escape(insertion_value)}\'|ez-toc-data-id="#{re.escape(insertion_value)}").*?</h[1-6]>)'

# For text-based matching:
heading_pattern = rf'(<h[1-6][^>]*>.*?{re.escape(insertion_value)}.*?</h[1-6]>)'
```

## 📝 Usage Examples

### Example 1: Configure for Coin Master Post
```bash
curl -X POST "https://smartlink-api-601738079869.us-central1.run.app/config/post" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 12345,
    "source_urls": ["https://example.com/links"],
    "insertion_point": {
      "type": "after_heading_id",
      "value": "Coin_Master_Free_Spins_Coins_Links"
    }
  }'
```

### Example 2: Update Existing Post Config
```bash
curl -X PATCH "https://smartlink-api-601738079869.us-central1.run.app/config/post/12345" \
  -H "Content-Type: application/json" \
  -d '{
    "insertion_point": {
      "type": "after_heading_text",
      "value": "Today's Links"
    }
  }'
```

### Example 3: Revert to Default (Prepend)
```bash
curl -X PATCH "https://smartlink-api-601738079869.us-central1.run.app/config/post/12345" \
  -H "Content-Type: application/json" \
  -d '{
    "insertion_point": null
  }'
```

## 🚀 Deployment Steps

1. **Test locally** (optional):
   ```bash
   cd /home/deepak/data/SmartLinkUpdater/backend
   python test_insertion_point.py
   ```

2. **Deploy to Cloud Run**:
   ```bash
   cd /home/deepak/data/SmartLinkUpdater/backend
   gcloud run deploy smartlink-api \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

3. **Verify deployment**:
   ```bash
   curl https://smartlink-api-601738079869.us-central1.run.app/health
   ```

4. **Test with your Coin Master post**:
   ```bash
   # Update config
   curl -X PATCH "https://smartlink-api-601738079869.us-central1.run.app/config/post/YOUR_POST_ID" \
     -H "Content-Type: application/json" \
     -d '{
       "insertion_point": {
         "type": "after_heading_id",
         "value": "Coin_Master_Free_Spins_Coins_Links"
       }
     }'
   
   # Trigger update
   curl -X POST "https://smartlink-api-601738079869.us-central1.run.app/update-post/YOUR_POST_ID?sync=true"
   ```

## ✅ Testing Checklist

- [ ] Test prepend mode (default)
- [ ] Test after_heading_id with Coin Master post
- [ ] Test after_heading_text mode
- [ ] Test fallback when heading not found
- [ ] Test with simple headings (no ez-toc)
- [ ] Verify old sections still pruned correctly
- [ ] Test batch updates preserve insertion_point

## 🔮 Future Enhancements (Optional)

1. **WordPress UI**: Add dropdown in dashboard to configure insertion point per post
2. **Multiple insertion points**: Support inserting at multiple locations
3. **Position types**: Add `after_paragraph_N`, `before_heading_id`, etc.
4. **Preview mode**: Show where links will be inserted before updating

## 📊 Impact Assessment

- **Breaking changes**: None (backward compatible)
- **Default behavior**: Unchanged (still prepends if not configured)
- **Database changes**: New optional field (no migration needed)
- **Performance**: Minimal (one extra regex search per update)

## 🐛 Known Limitations

1. Only works with HTML-rendered headings (not Gutenberg blocks in edit mode)
2. Regex may fail with very complex heading structures
3. No validation that target heading exists before update

## 📚 Related Files

- `backend/app/main.py` - API endpoints and models
- `backend/app/mongo_models.py` - MongoDB schema
- `backend/app/wp.py` - WordPress integration
- `backend/test_insertion_point.py` - Test script

---

**Version**: 2.3.0  
**Author**: SmartLink Team  
**Date**: November 8, 2025
