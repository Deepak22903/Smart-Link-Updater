#!/bin/bash
# Script to clean up old container images from Artifact Registry
# Usage: ./cleanup-old-images.sh [keep_count]
# Default: keeps last 3 images

KEEP_COUNT=${1:-3}
REPOSITORY="us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api"

echo "🔍 Listing all images..."
gcloud artifacts docker images list "$REPOSITORY" \
  --sort-by=~CREATE_TIME \
  --format="table(version,createTime,tags)"

echo ""
echo "📊 Total images:"
TOTAL=$(gcloud artifacts docker images list "$REPOSITORY" --format="value(version)" | wc -l)
echo "$TOTAL images found"

if [ "$TOTAL" -le "$KEEP_COUNT" ]; then
  echo "✅ Only $TOTAL images exist. Nothing to delete (keeping $KEEP_COUNT)."
  exit 0
fi

echo ""
echo "🗑️  Will delete $(($TOTAL - $KEEP_COUNT)) old images (keeping newest $KEEP_COUNT)..."
read -p "Continue? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Cancelled"
  exit 1
fi

echo ""
echo "🧹 Deleting old images..."
gcloud artifacts docker images list "$REPOSITORY" \
  --sort-by=~CREATE_TIME \
  --format="get(version)" \
  | tail -n +$(($KEEP_COUNT + 1)) \
  | while read digest; do
    echo "  → Deleting: $digest"
    gcloud artifacts docker images delete \
      "$REPOSITORY@$digest" \
      --quiet 2>&1 | grep -v "Deleted" || true
  done

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining images:"
gcloud artifacts docker images list "$REPOSITORY" \
  --sort-by=~CREATE_TIME \
  --format="table(version,createTime,tags)"
