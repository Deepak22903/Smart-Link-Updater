# Firebase FCM - Cloud Run Deployment Guide

## 🚀 Deploy to Cloud Run with Firebase

Your backend code is ready! Now we need to deploy it to Cloud Run with the Firebase service account.

---

## 📦 Option 1: Deploy with Secret Manager (Recommended)

### Step 1: Upload Secret to Google Secret Manager

```bash
cd ~/path/to/Smart-Link-Updater

# Upload Firebase service account as secret
gcloud secrets create firebase-adminsdk \
  --data-file=firebase-adminsdk.json \
  --project=smart-link-updater

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding firebase-adminsdk \
  --member=serviceAccount:601738079869-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor \
  --project=smart-link-updater
```

### Step 2: Update deployCommands.sh

Add secret mounting:

```bash
#!/bin/bash
set -e

# ... existing build commands ...

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
  --port 8080 \
  --set-secrets=/app/firebase-adminsdk.json=firebase-adminsdk:latest

# ... rest of script ...
```

### Step 3: Update push_notifications.py path

```python
# In backend/app/push_notifications.py, update path:
cred_path = Path("/app/firebase-adminsdk.json")  # Cloud Run secret mount point
if not cred_path.exists():
    # Fallback to local path for development
    cred_path = Path(__file__).parent.parent.parent / "firebase-adminsdk.json"
```

### Step 4: Deploy

```bash
./deployCommands.sh
```

---

## 📦 Option 2: Include in Docker Image (Simpler, Less Secure)

### Step 1: Update Dockerfile

Add this line before the CMD:

```dockerfile
# Copy Firebase service account
COPY firebase-adminsdk.json /app/firebase-adminsdk.json
```

### Step 2: Deploy

```bash
./deployCommands.sh
```

**⚠️ Warning:** This includes the secret in the Docker image. Use Option 1 for production.

---

## 🧪 Test After Deployment

### 1. Verify Backend is Live

```bash
curl https://smartlink-api-601738079869.us-central1.run.app/health
```

### 2. Check Token Count

```bash
curl https://smartlink-api-601738079869.us-central1.run.app/api/notifications/tokens/count
```

### 3. Build App Development Build

```bash
cd ~/path/to/travel-rewards-app

# For Android
eas build --profile development --platform android

# Or local build
npx expo run:android
```

### 4. Install & Register

1. Install the development build on your device
2. Open the app
3. Check logs for: `✅ FCM token registered with backend`

### 5. Send Test Notification

```bash
curl -X POST https://smartlink-api-601738079869.us-central1.run.app/api/notifications/send/new-rewards \
  -H 'Content-Type: application/json' \
  -d '{"count": 5}'
```

**You should receive a push notification!** 🎉

---

## 🐛 Troubleshooting

### Firebase initialization fails?

Check Cloud Run logs:
```bash
gcloud run services logs read smartlink-api --limit 50
```

Look for:
- `Firebase service account key not found`
- `Failed to initialize Firebase Admin SDK`

### No notification received?

1. Check token registered: `/api/notifications/tokens/count`
2. Verify token type is `fcm` not `expo`
3. Check device notification settings
4. Verify app has FCM permissions

### Build fails?

Make sure firebase-admin is in requirements.txt:
```bash
cat requirements.txt | grep firebase
```

---

## 📊 Current Status

- ✅ Backend code updated for FCM
- ✅ Pushed to GitHub
- ✅ Firebase service account ready
- ⏳ Deploy to Cloud Run (you do this)
- ⏳ Build app development build
- ⏳ Test notifications

---

## 🎯 Quick Deploy Commands

**Option 1 (Secret Manager):**
```bash
cd ~/path/to/Smart-Link-Updater
gcloud secrets create firebase-adminsdk --data-file=firebase-adminsdk.json --project=smart-link-updater
gcloud secrets add-iam-policy-binding firebase-adminsdk --member=serviceAccount:601738079869-compute@developer.gserviceaccount.com --role=roles/secretmanager.secretAccessor --project=smart-link-updater
# Update deployCommands.sh with --set-secrets flag
./deployCommands.sh
```

**Option 2 (Docker Image):**
```bash
cd ~/path/to/Smart-Link-Updater
# Add COPY line to Dockerfile
./deployCommands.sh
```

---

**Let me know which option you want to use, and I'll help you deploy!** 🚀
