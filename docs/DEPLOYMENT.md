# Google Cloud Run Deployment Guide

## Prerequisites
✅ Google Cloud SDK installed
✅ Docker installed
✅ Google Cloud account (free tier available)

## Step 1: Initialize Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Create a new project (or use existing)
gcloud projects create smartlink-updater-prod --name="SmartLink Updater"

# Set the project
gcloud config set project smartlink-updater-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## Step 2: Store Secrets

Store sensitive credentials in Google Secret Manager:

```bash
# Store WordPress credentials
echo -n "https://your-site.com" | gcloud secrets create WP_BASE_URL --data-file=-
echo -n "your-username" | gcloud secrets create WP_USERNAME --data-file=-
echo -n "your-app-password" | gcloud secrets create WP_PASSWORD --data-file=-

# Store Gemini API key
echo -n "your-gemini-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

## Step 3: Build and Push Docker Image

```bash
# Set region
export REGION=us-central1

# Create Artifact Registry repository
gcloud artifacts repositories create smartlink-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="SmartLink Updater Docker repository"

# Configure Docker to use gcloud credentials
gcloud auth configure-docker $REGION-docker.pkg.dev

# Build the Docker image
docker build -t $REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest .

# Push to Artifact Registry
docker push $REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest
```

## Step 4: Deploy to Cloud Run

```bash
gcloud run deploy smartlink-api \
    --image=$REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest \
    --platform=managed \
    --region=$REGION \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=3 \
    --set-secrets="WP_BASE_URL=WP_BASE_URL:latest,WP_USERNAME=WP_USERNAME:latest,WP_PASSWORD=WP_PASSWORD:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

## Step 5: Get Your Public URL

After deployment, Cloud Run will provide a URL like:
```
https://smartlink-api-xxxxxxxxxx-uc.a.run.app
```

## Step 6: Test the Deployment

```bash
# Health check
curl https://smartlink-api-xxxxxxxxxx-uc.a.run.app/health

# Update a post
curl -X POST https://smartlink-api-xxxxxxxxxx-uc.a.run.app/update-post/4166
```

## Cost Estimate (Free Tier)

Google Cloud Run free tier includes:
- 2 million requests per month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

With hourly checks (24/day × 30 = 720 requests/month), you'll stay well within free tier limits.

## Monitoring

View logs in Cloud Console:
```bash
gcloud run services logs read smartlink-api --region=$REGION --limit=50
```

## Environment Variables (Alternative to Secrets)

If you prefer environment variables instead of Secret Manager:

```bash
gcloud run deploy smartlink-api \
    --set-env-vars="WP_BASE_URL=https://your-site.com,WP_USERNAME=admin,WP_PASSWORD=xxxx,GEMINI_API_KEY=xxxx"
```

## Updating the Service

After making code changes:

```bash
# Rebuild and push
docker build -t $REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest .
docker push $REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest

# Redeploy (Cloud Run will automatically use the new image)
gcloud run deploy smartlink-api --image=$REGION-docker.pkg.dev/smartlink-updater-prod/smartlink-repo/api:latest --region=$REGION
```

## Troubleshooting

**Issue: Container fails to start**
```bash
# Check logs
gcloud run services logs read smartlink-api --region=$REGION

# Common issues:
# - Missing environment variables
# - Port binding (Cloud Run sets PORT env var)
# - Startup timeout (increase with --timeout=300)
```

**Issue: 403 Forbidden**
```bash
# Make service public
gcloud run services add-iam-policy-binding smartlink-api \
    --region=$REGION \
    --member="allUsers" \
    --role="roles/run.invoker"
```

## Next Steps

Once deployed:
1. ✅ Get the public URL
2. ✅ Test all endpoints
3. ✅ Update WordPress plugin with the URL
4. ✅ Set up Cloud Scheduler for automatic hourly updates (optional)
