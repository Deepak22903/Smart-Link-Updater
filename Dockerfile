# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ backend/
COPY .env .env

# Copy Firebase service account (if exists, for simpler deployment)
# For production, use Secret Manager instead (see FIREBASE_DEPLOY_GUIDE.md)
COPY firebase-adminsdk*.json ./firebase-adminsdk.json 2>/dev/null || true

# Create data directory for runtime files (MongoDB handles data persistence)
RUN mkdir -p backend/data

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Run the application
CMD uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
