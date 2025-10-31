# 🎉 SmartLink Updater - DEPLOYED!

## ✅ Deployment Complete

**Service URL:** https://smartlink-api-601738079869.us-central1.run.app

**Project:** smart-link-updater  
**Region:** us-central1  
**Status:** LIVE ✅

---

## 📡 API Endpoints

### Health Check
```bash
curl https://smartlink-api-601738079869.us-central1.run.app/health
```

### List Configured Posts
```bash
curl https://smartlink-api-601738079869.us-central1.run.app/config/posts
```

### Get Post Configuration
```bash
curl https://smartlink-api-601738079869.us-central1.run.app/config/post/4166
```

### Update Post (Main Endpoint)
```bash
curl -X POST https://smartlink-api-601738079869.us-central1.run.app/update-post/4166
```

---

## 🔑 Environment Variables (Configured)

- ✅ WP_BASE_URL
- ✅ WP_USERNAME
- ✅ WP_APPLICATION_PASSWORD
- ✅ GEMINI_API_KEY
- ✅ TIMEZONE
- ✅ GEMINI_MIN_CONFIDENCE

---

## 📊 Resource Configuration

- **Memory:** 512 MB
- **CPU:** 1 vCPU
- **Max Instances:** 10
- **Authentication:** Public (allow-unauthenticated)

---

## 💰 Cost Estimate

**Free Tier Includes:**
- 2 million requests/month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**Your Usage (hourly checks):**
- ~720 requests/month (24/day × 30)
- Well within free tier! 💯

---

## 🔄 Next Steps

### 1. Test the Deployment
```bash
# Test health
curl https://smartlink-api-601738079869.us-central1.run.app/health

# Test update
curl -X POST https://smartlink-api-601738079869.us-central1.run.app/update-post/4166
```

### 2. Create WordPress Plugin
Use the service URL in your WordPress plugin to trigger updates from the admin panel.

### 3. Set Up Automated Updates (Optional)
Create a Cloud Scheduler job to call the API hourly:

```bash
# Enable Cloud Scheduler API
gcloud services enable cloudscheduler.googleapis.com

# Create hourly job
gcloud scheduler jobs create http smartlink-hourly-update \
    --location=us-central1 \
    --schedule="0 * * * *" \
    --uri="https://smartlink-api-601738079869.us-central1.run.app/update-post/4166" \
    --http-method=POST \
    --description="Update SmartLink post 4166 hourly"

# For post 4163 (Carnival Tycoon)
gcloud scheduler jobs create http smartlink-hourly-update-4163 \
    --location=us-central1 \
    --schedule="5 * * * *" \
    --uri="https://smartlink-api-601738079869.us-central1.run.app/update-post/4163" \
    --http-method=POST \
    --description="Update SmartLink post 4163 hourly"
```

---

## 🛠️ Management Commands

### View Logs
```bash
gcloud run services logs read smartlink-api --region=us-central1 --limit=50
```

### View Service Details
```bash
gcloud run services describe smartlink-api --region=us-central1
```

### Update Service (After Code Changes)
```bash
# Rebuild image
gcloud builds submit --tag us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest

# Deploy new version (Cloud Run auto-deploys from latest tag)
gcloud run deploy smartlink-api --image=us-central1-docker.pkg.dev/smart-link-updater/smartlink-repo/api:latest --region=us-central1
```

### Delete Service (if needed)
```bash
gcloud run services delete smartlink-api --region=us-central1
```

---

## 🔐 Security Notes

- Service is publicly accessible (no auth required)
- Consider adding API key authentication for production
- WordPress credentials are stored as environment variables (consider using Secret Manager for better security)
- HTTPS is enforced by default

---

## 📱 WordPress Plugin Next

Create a simple plugin with this code structure:

```php
<?php
/*
Plugin Name: SmartLink Updater
Description: Update post links with one click
Version: 1.0
*/

add_action('add_meta_boxes', 'smartlink_add_update_button');

function smartlink_add_update_button() {
    add_meta_box(
        'smartlink_update',
        'SmartLink Updater',
        'smartlink_render_button',
        'post',
        'side',
        'high'
    );
}

function smartlink_render_button($post) {
    $api_url = 'https://smartlink-api-601738079869.us-central1.run.app/update-post/' . $post->ID;
    ?>
    <button type="button" id="smartlink-update-btn" class="button button-primary button-large">
        Update Links
    </button>
    <div id="smartlink-result"></div>
    
    <script>
    jQuery('#smartlink-update-btn').on('click', function() {
        var btn = jQuery(this);
        btn.prop('disabled', true).text('Updating...');
        
        jQuery.ajax({
            url: '<?php echo $api_url; ?>',
            method: 'POST',
            success: function(data) {
                jQuery('#smartlink-result').html(
                    '<p style="color:green;">✅ ' + data.message + '</p>'
                );
                btn.prop('disabled', false).text('Update Links');
            },
            error: function() {
                jQuery('#smartlink-result').html(
                    '<p style="color:red;">❌ Update failed</p>'
                );
                btn.prop('disabled', false).text('Update Links');
            }
        });
    });
    </script>
    <?php
}
```

---

## 🎯 Features Working

- ✅ Scraping (httpx)
- ✅ Gemini AI extraction
- ✅ Deduplication (fingerprints)
- ✅ WordPress REST API integration
- ✅ Auto-pruning (keeps last 5 days)
- ✅ Styled buttons (pink border, blue hover)
- ✅ Green centered h4 headings

---

## 📞 Support

**View in Cloud Console:**  
https://console.cloud.google.com/run/detail/us-central1/smartlink-api/metrics?project=smart-link-updater

**Cloud Build History:**  
https://console.cloud.google.com/cloud-build/builds?project=smart-link-updater
