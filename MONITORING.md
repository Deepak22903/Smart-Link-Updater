# HTML Structure Monitoring System

## Overview

Automatically detects when source websites change their HTML structure, which would break link extractors. Provides alerts via email, webhooks (Slack/Discord), and API endpoints for monitoring.

## Features

### 1. **HTML Structure Fingerprinting**
- Computes unique fingerprint of HTML structure (DOM hash, headings, selectors)
- Tracks changes in:
  - DOM structure
  - Heading hierarchy
  - CSS selectors
  - Page size
  - Link count

### 2. **Extraction History Tracking**
- Records every extraction attempt with:
  - Date
  - Links found
  - Confidence score
  - Success/failure status
  - Error messages
- Stores last 30 days of history per source

### 3. **Automatic Alert Generation**

Alerts trigger on:

| Alert Type | Condition | Severity |
|------------|-----------|----------|
| `structure_changed` | DOM hash different, selectors missing | Warning |
| `zero_links` | 0 links extracted (after 12 PM) | Critical |
| `low_confidence` | Confidence < 0.5 (usually > 0.8) | Warning |
| `link_count_drop` | 50%+ decrease in links | Warning |
| `consecutive_failures` | 3+ failed extractions in a row | Critical |

### 4. **Multiple Notification Channels**

- **Console**: Always logged (for development)
- **Email**: SMTP with HTML formatting
- **Webhooks**: Slack, Discord, or custom endpoints

### 5. **Health Dashboard API**

Monitor all sources via REST API:
- Individual source health
- All sources overview
- Recent alerts
- Unnotified alerts

## Setup

### 1. Environment Variables

Add to `.env`:

```env
# Email Alerts (via SMTP)
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_FROM=smartlink@yoursite.com
ALERT_EMAIL_TO=admin@yoursite.com

# Webhook Alerts (Slack, Discord, or custom)
ENABLE_WEBHOOK_ALERTS=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Console Alerts
ENABLE_CONSOLE_ALERTS=true

# API URL (for links in email alerts)
API_URL=https://smartlink-api-601738079869.us-central1.run.app
```

### 2. Email Setup (Gmail)

1. Go to https://myaccount.google.com/apppasswords
2. Generate an "App Password"
3. Use it as `SMTP_PASSWORD` (not your Gmail password)

### 3. Slack Webhook Setup

1. Go to https://api.slack.com/messaging/webhooks
2. Create a new Incoming Webhook
3. Copy the webhook URL to `ALERT_WEBHOOK_URL`

### 4. Discord Webhook Setup

1. Go to Server Settings → Integrations → Webhooks
2. Create a new webhook
3. Copy the webhook URL to `ALERT_WEBHOOK_URL`

## Usage

### Automatic Monitoring

Monitoring happens automatically during link extraction:

```python
# In main.py, during extraction:
monitor.record_extraction(
    source_url=url,
    date=today_iso,
    links_found=len(links),
    confidence=0.9,
    success=True,
    html=html  # Automatically fingerprints structure
)
```

### API Endpoints

#### Get All Source Health Statuses
```bash
curl https://your-api.run.app/health/extractors
```

Response:
```json
{
  "https://example.com/rewards": {
    "status": "healthy",
    "consecutive_failures": 0,
    "last_check": "2025-10-27T10:30:00",
    "recent_stats": {
      "avg_links": 8.5,
      "avg_confidence": 0.92,
      "success_rate": 100.0
    },
    "fingerprint": {
      "dom_hash": "abc123",
      "heading_count": 15,
      "link_count": 45,
      "html_size": 45000
    }
  }
}
```

#### Get Recent Alerts
```bash
curl https://your-api.run.app/alerts?hours=24
```

Response:
```json
{
  "alerts": [
    {
      "alert_type": "zero_links",
      "source_url": "https://example.com/rewards",
      "severity": "critical",
      "message": "Zero links extracted today",
      "timestamp": "2025-10-27T14:00:00",
      "details": {
        "date": "2025-10-27",
        "attempts": 3
      }
    }
  ],
  "count": 1
}
```

#### Send Pending Notifications
```bash
curl -X POST https://your-api.run.app/alerts/send
```

Response:
```json
{
  "processed": 3,
  "total_alerts": 3,
  "message": "Sent 3 notifications"
}
```

### Scheduled Notification Check

#### Option 1: Cloud Scheduler (Production)

Create a Cloud Scheduler job to check alerts hourly:

```bash
gcloud scheduler jobs create http check-monitoring-alerts \
  --schedule="0 * * * *" \
  --uri="https://smartlink-api-601738079869.us-central1.run.app/alerts/send" \
  --http-method=POST \
  --location=us-central1
```

#### Option 2: Cron Job (Local Server)

Add to crontab:
```cron
# Check for alerts every hour
0 * * * * curl -X POST http://localhost:8000/alerts/send
```

#### Option 3: Manual Trigger

Call the endpoint manually whenever you want to check:
```bash
curl -X POST http://localhost:8000/alerts/send
```

## Testing

### Run Test Suite

```bash
python3 test_monitoring.py
```

Tests:
1. ✅ HTML fingerprint generation
2. ✅ Structure change detection
3. ✅ Extraction history tracking
4. ✅ Alert generation (zero links, structure changes)
5. ✅ Real website monitoring
6. ✅ Health dashboard

### Manual Testing

1. **Test Email Notifications**:
   ```bash
   # Set ENABLE_EMAIL_ALERTS=true in .env
   # Trigger an alert by having zero extractions
   curl -X POST http://localhost:8000/alerts/send
   ```

2. **Test Webhook Notifications**:
   ```bash
   # Set ENABLE_WEBHOOK_ALERTS=true in .env
   curl -X POST http://localhost:8000/alerts/send
   ```

3. **Simulate Structure Change**:
   ```python
   # Edit a test extractor to return 0 links
   # Run extraction
   # Check alerts endpoint
   ```

## Data Files

Monitoring data is stored in `backend/data/`:

### `monitoring.json`
```json
{
  "https://example.com/rewards": {
    "source_url": "https://example.com/rewards",
    "fingerprint": {
      "dom_hash": "abc123",
      "heading_structure": ["h2:Working Links", "h3:26 October"],
      "critical_selectors": [".reward-link"],
      "html_size": 45000,
      "heading_count": 15,
      "link_count": 45
    },
    "extraction_history": [
      {
        "date": "2025-10-27",
        "links_found": 8,
        "confidence": 0.92,
        "timestamp": "2025-10-27T10:30:00",
        "success": true
      }
    ],
    "last_check": "2025-10-27T10:30:00",
    "status": "healthy",
    "consecutive_failures": 0
  }
}
```

### `alerts.json`
```json
[
  {
    "alert_type": "structure_changed",
    "source_url": "https://example.com/rewards",
    "severity": "warning",
    "message": "HTML structure changed",
    "timestamp": "2025-10-27T09:00:00",
    "notified": true,
    "details": {
      "reasons": [
        "DOM structure changed (hash: abc123 → def456)",
        "Missing selectors: .reward-link"
      ]
    }
  }
]
```

## Alert Details

### Structure Changed Alert

**Triggers when:**
- DOM hash is different
- Heading count changes by >20%
- Page size changes by >40%
- Critical CSS selectors disappear

**Example:**
```
🔔 SmartLink Updater Alert
Type: structure_changed
Severity: warning

Source: https://example.com/rewards
Message: HTML structure changed for https://example.com/rewards

Details:
- DOM structure changed (hash: abc123 → def456)
- Heading count changed significantly: 15 → 8
- Missing selectors: .reward-link
```

### Zero Links Alert

**Triggers when:**
- 0 links extracted from a source
- After 12 PM (to avoid false alarms from early morning checks)

**Example:**
```
🚨 SmartLink Updater Alert
Type: zero_links
Severity: critical

Source: https://example.com/rewards
Message: Zero links extracted today from https://example.com/rewards

Details:
- date: 2025-10-27
- attempts: 3
```

### Low Confidence Alert

**Triggers when:**
- Current confidence < 0.5
- Historical average > 0.7
- Indicates AI is uncertain about extraction

**Example:**
```
⚠️ SmartLink Updater Alert
Type: low_confidence
Severity: warning

Source: https://example.com/rewards
Message: Confidence dropped significantly for https://example.com/rewards

Details:
- historical_avg: 0.85
- today_avg: 0.42
```

## Troubleshooting

### No Alerts Received

1. **Check console logs**: Alerts are always logged
2. **Verify email credentials**: Test with Gmail App Password
3. **Check webhook URL**: Ensure Slack/Discord webhook is valid
4. **Trigger manually**: `curl -X POST .../alerts/send`

### False Positives

**Too many structure change alerts:**
- Increase thresholds in `html_monitor.py`:
  ```python
  heading_diff > 0.2  # Change to 0.3 (30% variance)
  size_diff > 0.4     # Change to 0.5 (50% variance)
  ```

**Zero link alerts too early:**
- Adjust time threshold in `html_monitor.py`:
  ```python
  if current_hour >= 12:  # Change to 14 (2 PM)
  ```

### Monitoring Data Growing Too Large

Files are automatically pruned:
- Extraction history: Last 30 days only
- Alerts: Last 100 alerts only

## Architecture

```
┌─────────────────┐
│  Extraction     │
│  (main.py)      │
└────────┬────────┘
         │ record_extraction()
         ▼
┌─────────────────┐
│  HTMLMonitor    │──────► monitoring.json
│  (html_monitor) │        (fingerprints, history)
└────────┬────────┘
         │ check_alert_conditions()
         ▼
┌─────────────────┐
│  Alerts         │──────► alerts.json
│  (html_monitor) │        (alert records)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notification    │──────► Email, Slack, Discord
│ (notifications) │
└─────────────────┘
```

## Best Practices

1. **Set up notifications early**: Don't wait for production failures
2. **Test with real extractions**: Run actual updates to generate fingerprints
3. **Monitor the dashboard**: Check `/health/extractors` regularly
4. **Adjust thresholds**: Fine-tune based on your specific sites
5. **Use Cloud Scheduler**: Automate alert checks hourly in production

## Future Enhancements

Potential additions:
- [ ] SMS notifications via Twilio
- [ ] PagerDuty integration
- [ ] Grafana dashboard
- [ ] Machine learning for anomaly detection
- [ ] Auto-fix: Attempt Gemini extractor when custom fails
- [ ] Historical trend analysis
- [ ] Weekly summary reports

## Support

For issues or questions:
1. Check logs in `backend/data/monitoring.json` and `alerts.json`
2. Run `python3 test_monitoring.py` to validate setup
3. Check API health: `curl .../health/extractors`
