# HTML Monitoring - Quick Start

## 🚀 5-Minute Setup

### 1. Enable Monitoring (Already Active!)

Monitoring is **automatically enabled** - no code changes needed. Every extraction is tracked.

### 2. Check Health Status

```bash
# View all sources
curl http://localhost:8000/health/extractors

# View specific source
curl "http://localhost:8000/health/extractors/https://example.com/rewards"
```

### 3. View Alerts

```bash
# Recent alerts (last 24 hours)
curl http://localhost:8000/alerts

# Unnotified alerts
curl http://localhost:8000/alerts/unnotified
```

### 4. Enable Notifications

#### Option A: Console Only (Default)
Already enabled - alerts print to console.

#### Option B: Email Alerts

Add to `.env`:
```env
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Get from https://myaccount.google.com/apppasswords
ALERT_EMAIL_TO=admin@yoursite.com
```

Test:
```bash
curl -X POST http://localhost:8000/alerts/send
```

#### Option C: Slack Alerts

Add to `.env`:
```env
ENABLE_WEBHOOK_ALERTS=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Test:
```bash
curl -X POST http://localhost:8000/alerts/send
```

### 5. Automate Alert Checks (Production)

```bash
# Cloud Scheduler (hourly)
gcloud scheduler jobs create http check-alerts \
  --schedule="0 * * * *" \
  --uri="https://your-api.run.app/alerts/send" \
  --http-method=POST \
  --location=us-central1
```

## 📊 What Gets Monitored

✅ **HTML Structure Changes**
- DOM hash changes
- Missing CSS selectors
- Heading structure changes
- Page size anomalies (±40%)

✅ **Extraction Failures**
- Zero links extracted (after 12 PM)
- Low confidence scores
- Consecutive failures (3+)
- 50%+ drop in link count

✅ **Health Metrics**
- Links found per extraction
- Confidence scores
- Success/failure rates
- Last 30 days of history

## 🔔 Alert Severities

| Severity | Examples |
|----------|----------|
| 🔵 **Info** | Structure fingerprint updated |
| ⚠️ **Warning** | Structure changed, low confidence, link count drop |
| 🚨 **Critical** | Zero links extracted, 3+ consecutive failures |

## 📁 Data Files

```
backend/data/
├── monitoring.json    # Fingerprints & extraction history
└── alerts.json        # Alert history
```

## 🧪 Test the System

```bash
# Run full test suite
python3 test_monitoring.py

# Check what's being monitored
curl http://localhost:8000/health/extractors

# Trigger a test alert
curl -X POST http://localhost:8000/alerts/send
```

## 🎯 Common Use Cases

### "Alert me when extractions fail"
```env
ENABLE_EMAIL_ALERTS=true
ALERT_EMAIL_TO=your-email@gmail.com
```
→ Automatically triggered on zero links or consecutive failures

### "Monitor in Slack"
```env
ENABLE_WEBHOOK_ALERTS=true
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/...
```
→ Real-time alerts in your Slack channel

### "Weekly health check"
```bash
# Add to cron (every Monday 9 AM)
0 9 * * 1 curl http://localhost:8000/health/extractors | mail -s "Weekly Health" admin@site.com
```

### "Get notified of structure changes"
Automatic - alerts trigger when:
- DOM hash changes
- Critical selectors disappear
- Page structure significantly different

## 🔧 Troubleshooting

**No data in monitoring.json?**
→ Run an extraction: `curl -X POST "http://localhost:8000/update-post/105?sync=true"`

**Alerts not sending?**
→ Check: `curl http://localhost:8000/alerts/unnotified`
→ Manually trigger: `curl -X POST http://localhost:8000/alerts/send`

**Too many false positives?**
→ Edit thresholds in `backend/app/html_monitor.py`:
```python
if heading_diff > 0.3:  # Increase from 0.2 to 0.3
if size_diff > 0.5:     # Increase from 0.4 to 0.5
```

## 📚 Full Documentation

See `MONITORING.md` for complete details.
