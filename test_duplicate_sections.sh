#!/bin/bash
# Test script to diagnose duplicate sections and fingerprint issues

echo "🔍 Testing SmartLink Updater - Duplicate Sections Diagnosis"
echo "============================================================"
echo ""

# Test 1: Get current fingerprints
echo "📊 Test 1: Checking stored fingerprints"
echo "----------------------------------------"
curl -s "http://127.0.0.1:8000/api/config/posts" | jq '.posts[] | select(.post_id == 111) | {post_id, content_slug}' > /tmp/post_config.json
cat /tmp/post_config.json
echo ""

# Test 2: First update (should add links)
echo "📝 Test 2: First update (should add new links)"
echo "----------------------------------------"
curl -s -X POST 'http://127.0.0.1:8000/update-post/111?sync=true' \
  -H 'Content-Type: application/json' | jq '{
    message,
    links_found,
    links_added,
    sections_pruned
  }'
echo ""
echo "⏱️  Wait 2 seconds..."
sleep 2

# Test 3: Second update immediately (should find duplicates)
echo "📝 Test 3: Second update (should find duplicates)"
echo "----------------------------------------"
curl -s -X POST 'http://127.0.0.1:8000/update-post/111?sync=true' \
  -H 'Content-Type: application/json' | jq '{
    message,
    links_found,
    links_added,
    sections_pruned
  }'
echo ""

# Test 4: Check batch history
echo "📚 Test 4: Recent batch history"
echo "----------------------------------------"
curl -s "http://127.0.0.1:8000/api/batch-history?limit=3" | jq '.history[] | {
  request_id: .request_id,
  total_posts: .total_posts,
  successful: .successful_posts,
  failed: .failed_posts,
  status: .overall_status
}'
echo ""

echo "============================================================"
echo "✅ Tests complete!"
echo ""
echo "🔍 Check your uvicorn server logs for detailed information:"
echo "   - Section removal logs"
echo "   - Fingerprint deduplication counts"
echo "   - Fingerprint saving confirmations"
echo ""
echo "Expected behavior:"
echo "   - First update: links_added > 0"
echo "   - Second update: links_added = 0 (all duplicates)"
echo "   - Sections pruned: should show old sections removed"
