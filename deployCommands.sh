#!/bin/bash
set -e

# Deploy new image
echo "Submitting build..."
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest .

echo "Deploying to Cloud Run..."
gcloud run deploy smartlink-api \
  --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --env-vars-file env-config.yaml \
  --port 8080

# Cleanup old images
echo "Cleaning up old images..."
KEEP_COUNT=1
REPOSITORY="us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api"

# Use --quiet to avoid interactive prompts and simplify parsing
TOTAL_IMAGES=$(gcloud artifacts docker images list "$REPOSITORY" --format="value(version)" --quiet | wc -l)

if [ "$TOTAL_IMAGES" -le "$KEEP_COUNT" ]; then
  echo "No old images to delete."
  exit 0
fi

echo "Keeping the latest $KEEP_COUNT image(s) and deleting the rest..."

# The --quiet flag on the delete command suppresses the confirmation prompt.
gcloud artifacts docker images list "$REPOSITORY" \
  --sort-by=~CREATE_TIME \
  --format="get(version)" \
  --quiet \
  | tail -n +$(($KEEP_COUNT + 1)) \
  | while read -r digest; do
      if [ -n "$digest" ]; then
        echo "Deleting image: $digest"
        gcloud artifacts docker images delete "$REPOSITORY@$digest" --quiet --delete-tags
      fi
    done

echo "Cleanup complete."