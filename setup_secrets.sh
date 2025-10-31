#!/bin/bash
# Script to create secrets in Google Cloud Secret Manager

echo "Creating secrets in Secret Manager..."

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create secrets
echo -n "https://wsopchipsfree.com" | gcloud secrets create WP_BASE_URL --data-file=- --replication-policy="automatic" 2>/dev/null || echo "WP_BASE_URL already exists"

echo -n "deepakshitole4@gmail.com" | gcloud secrets create WP_USERNAME --data-file=- --replication-policy="automatic" 2>/dev/null || echo "WP_USERNAME already exists"

echo -n "ph0Y9x6ToboyUVVPG2yTwLwD" | gcloud secrets create WP_APPLICATION_PASSWORD --data-file=- --replication-policy="automatic" 2>/dev/null || echo "WP_APPLICATION_PASSWORD already exists"

echo -n "AIzaSyCP1tbSLhJFh3e_aIAoxJdsJv1KaqQ6GHI" | gcloud secrets create GEMINI_API_KEY --data-file=- --replication-policy="automatic" 2>/dev/null || echo "GEMINI_API_KEY already exists"

echo -n "Asia/Kolkata" | gcloud secrets create TIMEZONE --data-file=- --replication-policy="automatic" 2>/dev/null || echo "TIMEZONE already exists"

echo -n "0.5" | gcloud secrets create GEMINI_MIN_CONFIDENCE --data-file=- --replication-policy="automatic" 2>/dev/null || echo "GEMINI_MIN_CONFIDENCE already exists"

echo "✅ All secrets created!"
echo ""
echo "To list secrets:"
echo "  gcloud secrets list"
