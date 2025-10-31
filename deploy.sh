#!/bin/bash
# Deploy to Cloud Run using Cloud Build (builds in the cloud, faster)

set -e

PROJECT_ID="smart-link-updater"
REGION="us-central1"
SERVICE_NAME="smartlink-api"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/smartlink-repo/api:latest"

echo "🚀 Deploying SmartLink Updater to Cloud Run..."
echo ""

# Step 1: Enable Cloud Build API
echo "📦 Enabling Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# Step 2: Build image using Cloud Build (faster than local)
echo "🔨 Building Docker image in the cloud..."
gcloud builds submit --tag ${IMAGE_NAME}

# Step 3: Deploy to Cloud Run
echo "🌐 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=10 \
    --set-env-vars="WP_BASE_URL=https://wsopchipsfree.com,WP_USERNAME=deepakshitole4@gmail.com,WP_APPLICATION_PASSWORD=ph0Y9x6ToboyUVVPG2yTwLwD,GEMINI_API_KEY=AIzaSyCP1tbSLhJFh3e_aIAoxJdsJv1KaqQ6GHI,TIMEZONE=Asia/Kolkata,GEMINI_MIN_CONFIDENCE=0.5,MONGODB_URI=mongodb+srv://deepakshitole4_db_user:6KiH8syvWCTNhh2D@smartlinkupdater.rpo4hmt.mongodb.net/SmartLinkUpdater?appName=SmartLinkUpdater,MONGODB_DATABASE=SmartLinkUpdater"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Get your service URL:"
echo "  gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format='value(status.url)'"
