gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest .
gcloud run deploy smartlink-api --image us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest --platform managed --region us-central1 --allow-unauthenticated --memory 512Mi --cpu 1 --max-instances 10 --env-vars-file env-config.yaml --port 8080
