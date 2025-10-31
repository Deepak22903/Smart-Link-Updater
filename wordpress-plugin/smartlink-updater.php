<?php
/**
 * Plugin Name: SmartLink Updater
 * Plugin URI: https://github.com/yourusername/smartlink-updater
 * Description: Automatically update post links with one click using Cloud Run API. Supports multiple WordPress sites, custom extractors, and Gemini AI.
 * Version: 2.0.0
 * Author: Your Name
 * Author URI: https://yourwebsite.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class SmartLinkUpdater {
    
    private $api_base_url = 'https://smartlink-api-601738079869.us-central1.run.app';
    
    public function __construct() {
        // Add meta box to post editor
        add_action('add_meta_boxes', array($this, 'add_update_button_metabox'));
        
        // Add admin menu page
        add_action('admin_menu', array($this, 'add_admin_menu'));
        
        // Handle AJAX request
        add_action('wp_ajax_smartlink_update', array($this, 'handle_update_request'));
        
        // Handle health check
        add_action('wp_ajax_smartlink_health_check', array($this, 'handle_health_check'));
        
        // Register REST API endpoints (server-side proxy)
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        
        // Enqueue scripts
        add_action('admin_enqueue_scripts', array($this, 'enqueue_scripts'));
    }
    
    /**
     * Add admin menu page
     */
    public function add_admin_menu() {
        add_menu_page(
            'SmartLink Updater',           // Page title
            'SmartLink',                    // Menu title
            'edit_posts',                   // Capability
            'smartlink-updater',            // Menu slug
            array($this, 'render_admin_page'), // Callback
            'dashicons-update',             // Icon
            30                              // Position
        );
    }
    
    /**
     * Add meta box with update button to post editor
     */
    public function add_update_button_metabox() {
        add_meta_box(
            'smartlink_updater',
            '🔗 SmartLink Updater',
            array($this, 'render_metabox'),
            'post',
            'side',
            'high'
        );
    }
    
    /**
     * Render the meta box content
     */
    public function render_metabox($post) {
        wp_nonce_field('smartlink_update_action', 'smartlink_update_nonce');
        ?>
        <div id="smartlink-updater-box">
            <p>Click the button below to fetch and update links from the configured source.</p>
            
            <button type="button" id="smartlink-update-btn" class="button button-primary button-large" style="width: 100%; margin-bottom: 10px;">
                <span class="dashicons dashicons-update" style="margin-top: 3px;"></span>
                Update Links Now
            </button>
            
            <div id="smartlink-status" style="margin-top: 10px;"></div>
            
            <div id="smartlink-result" style="margin-top: 10px; padding: 10px; border-left: 4px solid #ddd; background: #f9f9f9; display: none;">
                <strong>Last Update:</strong>
                <div id="smartlink-details"></div>
            </div>
        </div>
        
        <style>
            #smartlink-updater-box .spinner {
                float: none;
                margin: 0;
                visibility: visible;
            }
            #smartlink-status.success {
                color: #46b450;
            }
            #smartlink-status.error {
                color: #dc3232;
            }
            #smartlink-result.success {
                border-left-color: #46b450;
                background: #ecf7ed;
            }
            #smartlink-result.error {
                border-left-color: #dc3232;
                background: #f9e9e9;
            }
        </style>
        <?php
    }
    
    /**
     * Enqueue scripts for the admin panel
     */
    public function enqueue_scripts($hook) {
        // Load on post edit screen for meta box
        if ('post.php' === $hook || 'post-new.php' === $hook) {
            add_action('admin_footer', array($this, 'print_inline_script'));
        }
        
        // Load on admin page
        if ('toplevel_page_smartlink-updater' === $hook) {
            // Add dashboard CSS
            add_action('admin_head', array($this, 'print_dashboard_css'));
            add_action('admin_footer', array($this, 'print_admin_page_script'));
        }
    }
    
    /**
     * Print dashboard CSS
     */
    public function print_dashboard_css() {
        ?>
        <style>
        /* SmartLink Dashboard Styles - Modern & Colorful */
        .smartlink-dashboard-wrap {
            max-width: 1400px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen-Sans, Ubuntu, Cantarell, sans-serif;
        }

        .smartlink-dashboard-wrap h1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .smartlink-dashboard-wrap h1 .dashicons {
            font-size: 32px;
            width: 32px;
            height: 32px;
        }

        .smartlink-toast {
            position: fixed;
            top: 32px;
            right: 20px;
            padding: 15px 25px;
            border-radius: 12px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.15);
            z-index: 100000;
            font-weight: 600;
            min-width: 320px;
            animation: slideIn 0.3s ease-out;
            backdrop-filter: blur(10px);
        }

        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        .smartlink-toast.toast-success {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .smartlink-toast.toast-error {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
        }

        .smartlink-toast.toast-warning {
            background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%);
            color: #333;
        }

        .smartlink-toast.toast-info {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }

        .smartlink-batch-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 25px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border: none;
            border-radius: 12px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        .batch-controls-left,
        .batch-controls-right {
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }

        .batch-controls-left label {
            color: #555;
            font-weight: 600;
        }

        .smartlink-select {
            padding: 8px 12px;
            border: 2px solid #667eea;
            border-radius: 8px;
            background: white;
            font-weight: 600;
            color: #333;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .smartlink-select:hover {
            border-color: #764ba2;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
        }

        .smartlink-batch-progress {
            padding: 25px;
            background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
            border: none;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(142, 197, 252, 0.3);
        }

        .smartlink-batch-progress h3 {
            color: #333;
            margin-top: 0;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .smartlink-batch-progress h3 {
            margin-top: 0;
            margin-bottom: 15px;
        }

        .overall-progress {
            margin-bottom: 15px;
        }

        .progress-bar {
            width: 100%;
            height: 28px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 14px;
            overflow: hidden;
            margin-bottom: 8px;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
            position: relative;
        }

        .progress-bar.small {
            height: 20px;
            border-radius: 10px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.5s ease-out;
            position: relative;
            overflow: hidden;
            border-radius: 14px;
        }

        .progress-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            right: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.3),
                transparent
            );
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        .progress-text {
            font-size: 14px;
            color: #333;
            text-align: center;
            font-weight: 600;
        }

        .smartlink-table-container {
            background: white;
            border: none;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        .smartlink-posts-table {
            margin: 0;
            border-collapse: separate;
            border-spacing: 0;
        }

        .smartlink-posts-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .smartlink-posts-table th {
            color: white !important;
            font-weight: 600;
            padding: 16px 12px;
            text-align: left;
            border: none;
        }

        .smartlink-posts-table td {
            padding: 14px 12px;
            border-bottom: 1px solid #f0f0f0;
        }

        .smartlink-posts-table tbody tr {
            transition: all 0.2s ease;
        }

        .smartlink-posts-table tbody tr:hover {
            background: linear-gradient(135deg, #f8f9ff 0%, #fdf4ff 100%);
            transform: scale(1.01);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }

        .column-post-id {
            width: 80px;
        }

        .column-extractor {
            width: 120px;
        }

        .column-health {
            width: 100px;
        }

        .column-status {
            width: 150px;
        }

        .column-progress {
            width: 120px;
        }

        .column-actions {
            width: 180px;
        }

        .status-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .status-idle {
            background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%);
            color: #333;
        }

        .status-queued {
            background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
            color: #2d3436;
        }

        .status-running {
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .spin-icon {
            animation: spin 2s linear infinite;
            display: inline-block;
        }

        .status-success {
            background: linear-gradient(135deg, #55efc4 0%, #00b894 100%);
            color: white;
        }

        .status-no_changes {
            background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
            color: white;
        }

        .status-failed {
            background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
            color: white;
        }

        .status-partial {
            background: linear-gradient(135deg, #fab1a0 0%, #e17055 100%);
            color: white;
        }

        .status-message {
            display: block;
            margin-top: 4px;
            font-size: 11px;
            color: #666;
            font-weight: normal;
        }

        .health-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        .health-good {
            background: linear-gradient(135deg, #55efc4 0%, #00b894 100%);
            color: white;
        }

        .health-warning {
            background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
            color: white;
        }

        .health-critical {
            background: linear-gradient(135deg, #ff7675 0%, #d63031 100%);
            color: white;
        }

        .health-unknown {
            background: linear-gradient(135deg, #b2bec3 0%, #636e72 100%);
            color: white;
        }

        /* Button Enhancements */
        .button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 8px 16px !important;
            transition: all 0.3s ease !important;
            border: none !important;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
        }

        .button-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
        }

        .button-primary:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
        }

        .button-secondary {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
            color: white !important;
        }

        .button-secondary:hover {
            background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4) !important;
        }

        .button:not(.button-primary):not(.button-secondary) {
            background: white !important;
            color: #667eea !important;
            border: 2px solid #667eea !important;
        }

        .button:not(.button-primary):not(.button-secondary):hover {
            background: #667eea !important;
            color: white !important;
            transform: translateY(-2px);
        }

        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }

        .button-small {
            padding: 6px 12px !important;
            font-size: 13px !important;
        }

        .actions-cell {
            white-space: nowrap;
        }

        .button-small {
            font-size: 12px;
            padding: 4px 8px;
            height: auto;
            line-height: 1.4;
        }

        /* Modal */
        .smartlink-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(102, 126, 234, 0.3);
            backdrop-filter: blur(8px);
            z-index: 100000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .smartlink-modal-content {
            background: white;
            border-radius: 16px;
            width: 90%;
            max-width: 900px;
            max-height: 85vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
            from {
                transform: translateY(50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .smartlink-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 25px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px 16px 0 0;
        }

        .smartlink-modal-header h2 {
            margin: 0;
            font-size: 22px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .close-modal {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            cursor: pointer;
            padding: 8px;
            font-size: 24px;
            color: white;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }

        .close-modal:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: rotate(90deg);
        }

        .smartlink-modal-body {
            flex: 1;
            overflow-y: auto;
            padding: 25px 30px;
        }

        .log-content {
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 13px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 20px;
            border-radius: 12px;
            max-height: 450px;
            overflow-y: auto;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .log-line {
            padding: 8px 0;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            line-height: 1.5;
        }

        .log-line:last-child {
            border-bottom: none;
        }

        .smartlink-modal-footer {
            padding: 20px 30px;
            border-top: 2px solid #f0f0f0;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
            background: #fafafa;
            border-radius: 0 0 16px 16px;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .smartlink-batch-controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .batch-controls-left,
            .batch-controls-right {
                justify-content: space-between;
            }
            
            .smartlink-modal-content {
                width: 95%;
                max-height: 90vh;
            }
        }
        </style>
        <?php
    }
    
    /**
     * Print inline JavaScript
     */
    public function print_inline_script() {
        $post_id = get_the_ID();
        $ajax_url = admin_url('admin-ajax.php');
        $nonce = wp_create_nonce('smartlink_update_action');
        ?>
        <script type="text/javascript">
        jQuery(document).ready(function($) {
            $('#smartlink-update-btn').on('click', function(e) {
                e.preventDefault();
                
                var $btn = $(this);
                var $status = $('#smartlink-status');
                var $result = $('#smartlink-result');
                var $details = $('#smartlink-details');
                
                // Disable button and show loading
                $btn.prop('disabled', true).html('<span class="spinner is-active"></span> Updating...');
                $status.removeClass('success error').text('');
                $result.hide();
                
                // Make AJAX request
                $.ajax({
                    url: '<?php echo $ajax_url; ?>',
                    type: 'POST',
                    data: {
                        action: 'smartlink_update',
                        nonce: '<?php echo $nonce; ?>',
                        post_id: <?php echo $post_id; ?>
                    },
                    success: function(response) {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-update"></span> Update Links Now');
                        
                        if (response.success) {
                            var data = response.data;
                            var message = data.message || 'Update completed successfully';
                            
                            $status.addClass('success').html('✅ ' + message);
                            
                            // Show detailed results
                            var details = '<ul style="margin: 5px 0; padding-left: 20px;">';
                            details += '<li><strong>Links Found:</strong> ' + (data.links_found || 0) + '</li>';
                            details += '<li><strong>Links Added:</strong> ' + (data.links_added || 0) + '</li>';
                            
                            if (data.sections_pruned !== undefined) {
                                details += '<li><strong>Old Sections Removed:</strong> ' + data.sections_pruned + '</li>';
                            }
                            
                            if (data.date) {
                                details += '<li><strong>Date:</strong> ' + data.date + '</li>';
                            }
                            
                            details += '</ul>';
                            
                            $details.html(details);
                            $result.removeClass('error').addClass('success').fadeIn();
                            
                            // Reload the page after 2 seconds to show updated content
                            setTimeout(function() {
                                location.reload();
                            }, 2000);
                            
                        } else {
                            var errorMsg = response.data.message || response.data.detail || 'Update failed';
                            $status.addClass('error').html('❌ ' + errorMsg);
                            $details.html('<p>' + errorMsg + '</p>');
                            $result.removeClass('success').addClass('error').fadeIn();
                        }
                    },
                    error: function(xhr, status, error) {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-update"></span> Update Links Now');
                        
                        $status.addClass('error').html('❌ Request failed: ' + error);
                        $details.html('<p>Could not connect to the API server. Please try again.</p>');
                        $result.removeClass('success').addClass('error').fadeIn();
                    }
                });
            });
        });
        </script>
        <?php
    }
    
    /**
     * Print admin page JavaScript (NEW Real-Time Dashboard)
     */
    public function print_admin_page_script() {
        ?>
        <script type="text/javascript">
        jQuery(document).ready(function($) {
            const config = window.SmartLinkConfig;
            let currentBatchRequestId = null;
            let pollInterval = null;
            let postsData = [];
            
            // ========== INITIALIZATION ==========
            
            function init() {
                loadPosts();
                attachEventListeners();
            }
            
            function attachEventListeners() {
                $('#select-all-posts').on('click', selectAllPosts);
                $('#deselect-all-posts').on('click', deselectAllPosts);
                $('#batch-update-btn').on('click', startBatchUpdate);
                $('#refresh-posts').on('click', loadPosts);
                $('#cancel-batch').on('click', stopWatchingBatch);
                $('#cb-select-all').on('change', toggleAllCheckboxes);
                $('.close-modal').on('click', closeLogsModal);
                $('#refresh-logs').on('click', refreshLogs);
                
                // Delegate checkbox change event
                $(document).on('change', '.post-checkbox', updateSelectedCount);
                $(document).on('click', '.view-logs-btn', viewLogs);
                $(document).on('click', '.single-update-btn', singleUpdate);
            }
            
            // ========== LOAD POSTS ==========
            
            function loadPosts() {
                $.ajax({
                    url: config.restUrl + '/posts',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        postsData = response.posts || [];
                        renderPostsTable(postsData);
                    },
                    error: function(xhr) {
                        showToast('Failed to load posts: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            function renderPostsTable(posts) {
                const tbody = $('#posts-table-body');
                tbody.empty();
                
                if (posts.length === 0) {
                    tbody.append('<tr><td colspan="8" style="text-align: center; padding: 40px;">No configured posts found.</td></tr>');
                    return;
                }
                
                posts.forEach(function(post) {
                    const row = $('<tr>').attr('data-post-id', post.post_id);
                    
                    // Checkbox
                    row.append(
                        $('<th>').addClass('check-column').append(
                            $('<input>').attr({
                                type: 'checkbox',
                                class: 'post-checkbox',
                                value: post.post_id
                            })
                        )
                    );
                    
                    // Post ID
                    row.append($('<td>').text(post.post_id));
                    
                    // Title (fetch from WordPress if available)
                    const titleCell = $('<td>').text('Post ' + post.post_id);
                    row.append(titleCell);
                    
                    // Extractor
                    row.append($('<td>').text(post.extractor || 'default'));
                    
                    // Health Status
                    const healthBadge = getHealthBadge(post.health_status);
                    row.append($('<td>').html(healthBadge));
                    
                    // Status
                    const statusCell = $('<td>').addClass('status-cell').html(
                        '<span class="status-badge status-idle">Idle</span>'
                    );
                    row.append(statusCell);
                    
                    // Progress
                    const progressCell = $('<td>').addClass('progress-cell').html(
                        '<div class="progress-bar small"><div class="progress-fill" style="width: 0%;"></div></div>'
                    );
                    row.append(progressCell);
                    
                    // Actions
                    const actionsCell = $('<td>').addClass('actions-cell');
                    actionsCell.append(
                        $('<button>').addClass('button button-small single-update-btn').attr('data-post-id', post.post_id).html(
                            '<span class="dashicons dashicons-update"></span> Update'
                        )
                    );
                    actionsCell.append(' ');
                    actionsCell.append(
                        $('<button>').addClass('button button-small view-logs-btn').attr({
                            'data-post-id': post.post_id,
                            'disabled': true
                        }).html(
                            '<span class="dashicons dashicons-media-text"></span> Logs'
                        )
                    );
                    row.append(actionsCell);
                    
                    tbody.append(row);
                });
            }
            
            function getHealthBadge(status) {
                const badges = {
                    'healthy': '<span class="health-badge health-good">✓ Healthy</span>',
                    'warning': '<span class="health-badge health-warning">⚠ Warning</span>',
                    'critical': '<span class="health-badge health-critical">✗ Critical</span>',
                    'unknown': '<span class="health-badge health-unknown">? Unknown</span>'
                };
                return badges[status] || badges['unknown'];
            }
            
            // ========== SELECTION ==========
            
            function toggleAllCheckboxes() {
                const checked = $('#cb-select-all').prop('checked');
                $('.post-checkbox').prop('checked', checked);
                updateSelectedCount();
            }
            
            function selectAllPosts() {
                $('.post-checkbox').prop('checked', true);
                $('#cb-select-all').prop('checked', true);
                updateSelectedCount();
            }
            
            function deselectAllPosts() {
                $('.post-checkbox').prop('checked', false);
                $('#cb-select-all').prop('checked', false);
                updateSelectedCount();
            }
            
            function updateSelectedCount() {
                const count = $('.post-checkbox:checked').length;
                $('#selected-count').text(count);
                $('#batch-update-btn').prop('disabled', count === 0);
            }
            
            function getSelectedPostIds() {
                return $('.post-checkbox:checked').map(function() {
                    return parseInt($(this).val());
                }).get();
            }
            
            // ========== BATCH UPDATE ==========
            
            function startBatchUpdate() {
                const postIds = getSelectedPostIds();
                
                if (postIds.length === 0) {
                    showToast('Please select at least one post', 'warning');
                    return;
                }
                
                const target = $('#target-site-select').val() || 'this';
                
                if (!confirm('Start batch update for ' + postIds.length + ' post(s) on ' + target + '?')) {
                    return;
                }
                
                $('#batch-update-btn').prop('disabled', true);
                
                $.ajax({
                    url: config.restUrl + '/batch-update',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        post_ids: postIds,
                        sync: false,
                        target: target,
                        initiator: 'wordpress_dashboard'
                    }),
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        currentBatchRequestId = response.request_id;
                        showToast('Batch update started for ' + postIds.length + ' post(s)', 'success');
                        startPolling();
                        showBatchProgress(postIds.length);
                    },
                    error: function(xhr) {
                        showToast('Failed to start batch update: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                        $('#batch-update-btn').prop('disabled', false);
                    }
                });
            }
            
            function showBatchProgress(totalPosts) {
                $('#total-posts').text(totalPosts);
                $('#completed-posts').text(0);
                $('#overall-progress-fill').css('width', '0%');
                $('#batch-progress-container').slideDown();
            }
            
            function stopWatchingBatch() {
                stopPolling();
                $('#batch-progress-container').slideUp();
                $('#batch-update-btn').prop('disabled', false);
                loadPosts(); // Refresh table
            }
            
            // ========== POLLING ==========
            
            function startPolling() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                }
                
                pollInterval = setInterval(pollBatchStatus, config.pollInterval);
                pollBatchStatus(); // Initial poll
            }
            
            function stopPolling() {
                if (pollInterval) {
                    clearInterval(pollInterval);
                    pollInterval = null;
                }
                currentBatchRequestId = null;
            }
            
            function pollBatchStatus() {
                if (!currentBatchRequestId) {
                    stopPolling();
                    return;
                }
                
                $.ajax({
                    url: config.restUrl + '/batch-status/' + currentBatchRequestId,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        updateBatchUI(response);
                        
                        // Stop polling if batch is complete
                        if (response.overall_status === 'success' || response.overall_status === 'failed') {
                            stopPolling();
                            showToast('Batch update completed', 'success');
                            setTimeout(function() {
                                $('#batch-progress-container').slideUp();
                                $('#batch-update-btn').prop('disabled', false);
                            }, 3000);
                        }
                    },
                    error: function() {
                        // Continue polling even on error (might be temporary)
                    }
                });
            }
            
            function updateBatchUI(batchData) {
                const posts = batchData.posts || {};
                const postIds = Object.keys(posts);
                const totalPosts = postIds.length;
                let completedCount = 0;
                
                // Update each row
                postIds.forEach(function(postId) {
                    const postState = posts[postId];
                    const row = $('tr[data-post-id="' + postId + '"]');
                    
                    if (row.length === 0) return;
                    
                    // Update status badge
                    const statusBadge = getStatusBadge(postState.status, postState.message);
                    row.find('.status-cell').html(statusBadge);
                    
                    // Update progress bar
                    const progressWidth = postState.progress || 0;
                    row.find('.progress-fill').css('width', progressWidth + '%');
                    
                    // Enable logs button if there are logs
                    if (postState.log_count > 0) {
                        row.find('.view-logs-btn').prop('disabled', false);
                    }
                    
                    // Count completed
                    if (postState.status === 'success' || postState.status === 'failed') {
                        completedCount++;
                    }
                });
                
                // Update overall progress
                const overallProgress = Math.round((completedCount / totalPosts) * 100);
                $('#completed-posts').text(completedCount);
                $('#overall-progress-fill').css('width', overallProgress + '%');
            }
            
            function getStatusBadge(status, message) {
                const badges = {
                    'queued': '<span class="status-badge status-queued">⏳ Queued</span>',
                    'running': '<span class="status-badge status-running">▶ Running...</span>',
                    'success': '<span class="status-badge status-success">✓ Success</span>',
                    'no_changes': '<span class="status-badge status-no_changes">◉ No Changes</span>',
                    'failed': '<span class="status-badge status-failed">✗ Failed</span>',
                    'partial': '<span class="status-badge status-partial">⚠ Partial</span>'
                };
                
                const badge = badges[status] || '<span class="status-badge status-idle">Idle</span>';
                
                if (message) {
                    return badge + '<br><small class="status-message">' + escapeHtml(message) + '</small>';
                }
                
                return badge;
            }
            
            // ========== SINGLE UPDATE ==========
            
            function singleUpdate(e) {
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                if (!confirm('Update post ' + postId + '?')) {
                    return;
                }
                
                const btn = $(e.currentTarget);
                btn.prop('disabled', true);
                
                $.ajax({
                    url: config.restUrl + '/batch-update',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        post_ids: [postId],
                        sync: false,
                        target: 'this'
                    }),
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        currentBatchRequestId = response.request_id;
                        showToast('Update started for post ' + postId, 'success');
                        startPolling();
                    },
                    error: function(xhr) {
                        showToast('Failed to start update: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                        btn.prop('disabled', false);
                    }
                });
            }
            
            // ========== LOGS MODAL ==========
            
            function viewLogs(e) {
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                if (!currentBatchRequestId) {
                    showToast('No active batch request', 'warning');
                    return;
                }
                
                $('#log-post-id').text(postId);
                $('#log-content').html('<span class="spinner is-active"></span> Loading logs...');
                $('#logs-modal').fadeIn();
                
                loadLogs(postId);
            }
            
            function loadLogs(postId) {
                if (!currentBatchRequestId) return;
                
                $.ajax({
                    url: config.restUrl + '/batch-logs/' + currentBatchRequestId + '/' + postId,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        const logs = response.logs || [];
                        
                        if (logs.length === 0) {
                            $('#log-content').html('<p style="text-align: center; color: #666;">No logs available</p>');
                            return;
                        }
                        
                        const logHtml = logs.map(function(log) {
                            return '<div class="log-line">' + escapeHtml(log) + '</div>';
                        }).join('');
                        
                        $('#log-content').html(logHtml);
                        
                        // Auto-scroll to bottom
                        const logContainer = document.getElementById('log-content');
                        logContainer.scrollTop = logContainer.scrollHeight;
                    },
                    error: function() {
                        $('#log-content').html('<p style="text-align: center; color: #dc3232;">Failed to load logs</p>');
                    }
                });
            }
            
            function refreshLogs() {
                const postId = parseInt($('#log-post-id').text());
                loadLogs(postId);
            }
            
            function closeLogsModal() {
                $('#logs-modal').fadeOut();
            }
            
            // ========== TOAST NOTIFICATIONS ==========
            
            function showToast(message, type) {
                const toast = $('#smartlink-toast');
                toast.removeClass('toast-success toast-error toast-warning toast-info');
                toast.addClass('toast-' + type);
                toast.text(message);
                toast.fadeIn();
                
                setTimeout(function() {
                    toast.fadeOut();
                }, 4000);
            }
            
            // ========== UTILITIES ==========
            
            function escapeHtml(text) {
                const map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                };
                return text.replace(/[&<>"']/g, function(m) { return map[m]; });
            }
            
            // ========== START ==========
            
            init();
            // Check API status
            function checkApiStatus() {
                $('#api-status').text('Checking...').removeClass('online offline');
                
                $.ajax({
                    url: '<?php echo $ajax_url; ?>',
                    type: 'POST',
                    data: {
                        action: 'smartlink_health_check',
                        nonce: '<?php echo $nonce; ?>'
                    },
                    timeout: 10000,
                    success: function(response) {
                        if (response.success) {
                            $('#api-status').text('✅ Online').addClass('online');
                        } else {
                            $('#api-status').text('⚠️ Unknown').addClass('offline');
                        }
                    },
                    error: function() {
                        $('#api-status').text('❌ Offline').addClass('offline');
                    }
                });
            }
            
            checkApiStatus();
            $('#check-status-btn').on('click', checkApiStatus);
            
            // Populate target selects with configured sites from API
            function populateSiteSelects() {
                $.get('<?php echo $api_url; ?>/config/sites', function(resp) {
                    if (!resp || !resp.sites) return;
                    $('.smartlink-target-select').each(function() {
                        var $sel = $(this);
                        // Remove any existing site options (keep 'this' and 'all')
                        $sel.find('option[data-site-key]').remove();
                        $.each(resp.sites, function(key, info) {
                            var opt = $('<option>')
                                .attr('value', key)
                                .attr('data-site-key', key)
                                .text(key + ' — ' + info.base_url);
                            $sel.append(opt);
                        });
                    });
                }).fail(function() {
                    // ignore
                });
            }
            populateSiteSelects();
            // Update single post
            $('.smartlink-update-single').on('click', function() {
                var $btn = $(this);
                var postId = $btn.data('post-id');
                var $row = $btn.closest('tr');
                
                updatePost(postId, $btn, $row);
            });
            
            // Update all posts
            $('#update-all-btn').on('click', function() {
                var $btn = $(this);
                $btn.prop('disabled', true).html('<span class="spinner is-active" style="float:none;"></span> Updating all posts...');
                
                $('#update-results').html('<h2>Update Progress</h2>');
                
                var postIds = [];
                $('.smartlink-update-single').each(function() {
                    postIds.push($(this).data('post-id'));
                });
                
                var completed = 0;
                var total = postIds.length;
                
                function updateNext(index) {
                    if (index >= total) {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-update"></span> Update All Posts');
                        return;
                    }
                    
                    var postId = postIds[index];
                    var $row = $('tr[data-post-id="' + postId + '"]');
                    var $singleBtn = $('.smartlink-update-single[data-post-id="' + postId + '"]');
                    
                    updatePost(postId, $singleBtn, $row, function() {
                        completed++;
                        updateNext(index + 1);
                    });
                }
                
                updateNext(0);
            });
            
            function updatePost(postId, $btn, $row, callback) {
                $btn.prop('disabled', true).html('<span class="spinner is-active" style="float:none;"></span> Updating...');
                $row.addClass('updating');
                
                var target = $row.find('.smartlink-target-select').val() || 'this';
                $.ajax({
                    url: '<?php echo $ajax_url; ?>',
                    type: 'POST',
                    data: {
                        action: 'smartlink_update',
                        nonce: '<?php echo $nonce; ?>',
                        post_id: postId,
                        target: target
                    },
                    success: function(response) {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-update"></span> Update Now');
                        $row.removeClass('updating');
                        
                        if (response.success) {
                            var data = response.data;
                            var html = '<div class="update-result-item success">';
                            html += '<h3>✅ Post ' + postId + ' - ' + (data.message || 'Success') + '</h3>';
                            html += '<div class="update-stats">';
                            html += '<div><strong>Links Found:</strong> ' + (data.links_found || 0) + '</div>';
                            html += '<div><strong>Links Added:</strong> ' + (data.links_added || 0) + '</div>';
                            html += '<div><strong>Sections Pruned:</strong> ' + (data.sections_pruned || 0) + '</div>';
                            html += '</div>';
                            html += '</div>';
                            $('#update-results').append(html);
                        } else {
                            var errorMsg = response.data ? (response.data.message || response.data.detail || 'Unknown error') : 'Update failed';
                            var html = '<div class="update-result-item error">';
                            html += '<h3>❌ Post ' + postId + ' - ' + errorMsg + '</h3>';
                            html += '</div>';
                            $('#update-results').append(html);
                        }
                        
                        if (callback) callback();
                    },
                    error: function() {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-update"></span> Update Now');
                        $row.removeClass('updating');
                        
                        var html = '<div class="update-result-item error">';
                        html += '<h3>❌ Post ' + postId + ' - Request failed</h3>';
                        html += '</div>';
                        $('#update-results').append(html);
                        
                        if (callback) callback();
                    }
                });
            }
        });
        </script>
        <?php
    }
    
    /**
     * Render the admin page (NEW Real-Time Dashboard)
     */
    public function render_admin_page() {
        ?>
        <div class="wrap smartlink-dashboard-wrap">
            <h1>
                <span class="dashicons dashicons-update"></span>
                SmartLink Updater Dashboard
            </h1>
            
            <!-- Notification Toast -->
            <div id="smartlink-toast" class="smartlink-toast" style="display: none;"></div>
            
            <!-- Batch Controls -->
            <div class="smartlink-batch-controls">
                <div class="batch-controls-left">
                    <button type="button" id="select-all-posts" class="button">
                        <span class="dashicons dashicons-yes-alt"></span>
                        Select All
                    </button>
                    <button type="button" id="deselect-all-posts" class="button">
                        <span class="dashicons dashicons-dismiss"></span>
                        Deselect All
                    </button>
                    <label for="target-site-select" style="margin-left: 15px;">
                        <strong>Update Target:</strong>
                    </label>
                    <select id="target-site-select" class="smartlink-select" style="margin-left: 5px;">
                        <option value="this">This Site</option>
                        <option value="all">All Sites</option>
                        <!-- Dynamic options populated via API -->
                    </select>
                    <button type="button" id="batch-update-btn" class="button button-primary" disabled>
                        <span class="dashicons dashicons-update"></span>
                        Update Selected (<span id="selected-count">0</span>)
                    </button>
                </div>
                <div class="batch-controls-right">
                    <button type="button" id="refresh-posts" class="button">
                        <span class="dashicons dashicons-image-rotate"></span>
                        Refresh
                    </button>
                </div>
            </div>
            
            <!-- Active Batch Progress -->
            <div id="batch-progress-container" style="display: none;">
                <div class="smartlink-batch-progress">
                    <h3>
                        <span class="dashicons dashicons-update spin-icon"></span>
                        Batch Update in Progress
                    </h3>
                    <div class="overall-progress">
                        <div class="progress-bar">
                            <div id="overall-progress-fill" class="progress-fill"></div>
                        </div>
                        <div class="progress-text">
                            <span id="completed-posts">0</span> / <span id="total-posts">0</span> posts completed
                        </div>
                    </div>
                    <button type="button" id="cancel-batch" class="button button-secondary">
                        <span class="dashicons dashicons-no"></span>
                        Stop Watching
                    </button>
                </div>
            </div>
            
            <!-- Posts Table -->
            <div class="smartlink-table-container">
                <table class="wp-list-table widefat fixed striped smartlink-posts-table">
                    <thead>
                        <tr>
                            <td class="manage-column column-cb check-column">
                                <input type="checkbox" id="cb-select-all">
                            </td>
                            <th class="manage-column column-post-id">Post ID</th>
                            <th class="manage-column column-title">Title</th>
                            <th class="manage-column column-extractor">Extractor</th>
                            <th class="manage-column column-health">Health</th>
                            <th class="manage-column column-status">Status</th>
                            <th class="manage-column column-progress">Progress</th>
                            <th class="manage-column column-actions">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="posts-table-body">
                        <tr>
                            <td colspan="8" class="loading-row">
                                <span class="spinner is-active" style="float: none; margin: 0;"></span>
                                Loading posts...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Logs Modal -->
            <div id="logs-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content">
                    <div class="smartlink-modal-header">
                        <h2>Update Logs: Post <span id="log-post-id"></span></h2>
                        <button type="button" class="close-modal">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                    <div class="smartlink-modal-body">
                        <div id="log-content" class="log-content">
                            <span class="spinner is-active"></span>
                            Loading logs...
                        </div>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button close-modal">Close</button>
                        <button type="button" class="button" id="refresh-logs">
                            <span class="dashicons dashicons-image-rotate"></span>
                            Refresh
                        </button>
                    </div>
                </div>
            </div>
            
        </div>
        
        <script type="text/javascript">
        // Pass REST API URLs to JavaScript (server-side proxy)
        window.SmartLinkConfig = {
            restUrl: '<?php echo esc_url(rest_url('smartlink/v1')); ?>',
            nonce: '<?php echo wp_create_nonce('wp_rest'); ?>',
            pollInterval: 2000 // 2 seconds
        };
        </script>
        <?php
    }
    
    /**
     * Get configured posts from API
     */
    private function get_configured_posts() {
        $response = wp_remote_get($this->api_base_url . '/config/posts', array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return array();
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return isset($data['posts']) ? $data['posts'] : array();
    }
    
    /**
     * Handle AJAX health check request
     */
    public function handle_health_check() {
        check_ajax_referer('smartlink_update_action', 'nonce');
        
        $response = wp_remote_get($this->api_base_url . '/health', array(
            'timeout' => 5
        ));
        
        if (is_wp_error($response)) {
            wp_send_json_error(array('message' => 'Offline'));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (isset($data['status']) && $data['status'] === 'ok') {
            wp_send_json_success(array('status' => 'ok'));
        } else {
            wp_send_json_error(array('message' => 'Unknown'));
        }
    }
    
    /**
     * Register REST API routes (server-side proxy to Cloud Run)
     * This ensures no API secrets are exposed in client-side JavaScript
     */
    public function register_rest_routes() {
        // Batch update endpoint
        register_rest_route('smartlink/v1', '/batch-update', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_batch_update_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Batch status endpoint
        register_rest_route('smartlink/v1', '/batch-status/(?P<request_id>[a-zA-Z0-9-]+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_batch_status_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Post logs endpoint
        register_rest_route('smartlink/v1', '/batch-logs/(?P<request_id>[a-zA-Z0-9-]+)/(?P<post_id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_batch_logs_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // List posts endpoint
        register_rest_route('smartlink/v1', '/posts', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_list_posts_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // List extractors endpoint
        register_rest_route('smartlink/v1', '/extractors', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_list_extractors_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
    }

    /**
     * Handle batch update REST request (server-side proxy)
     */
    public function handle_batch_update_rest($request) {
        $post_ids = $request->get_param('post_ids');
        $sync = $request->get_param('sync') ?: false;
        $target = $request->get_param('target') ?: 'this';
        
        if (empty($post_ids) || !is_array($post_ids)) {
            return new WP_Error('invalid_post_ids', 'Invalid post_ids parameter', array('status' => 400));
        }
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/api/batch-update';
        
        $response = wp_remote_post($api_url, array(
            'timeout' => 60,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode(array(
                'post_ids' => array_map('intval', $post_ids),
                'sync' => (bool)$sync,
                'initiator' => 'wp-plugin-v2.1.0',
                'target' => $target
            ))
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }

    /**
     * Handle batch status REST request (server-side proxy)
     */
    public function handle_batch_status_rest($request) {
        $request_id = $request->get_param('request_id');
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/api/batch-status/' . urlencode($request_id);
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }

    /**
     * Handle batch logs REST request (server-side proxy)
     */
    public function handle_batch_logs_rest($request) {
        $request_id = $request->get_param('request_id');
        $post_id = $request->get_param('post_id');
        $tail = $request->get_param('tail') ?: 50;
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/api/batch-logs/' . urlencode($request_id) . '/' . intval($post_id) . '?tail=' . intval($tail);
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }

    /**
     * Handle list posts REST request (server-side proxy)
     */
    public function handle_list_posts_rest($request) {
        $api_url = $this->api_base_url . '/api/posts/list';
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }

    /**
     * Handle list extractors REST request (server-side proxy)
     */
    public function handle_list_extractors_rest($request) {
        $api_url = $this->api_base_url . '/api/extractors/list';
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Poll the task status endpoint and display results/errors.
     */
    private function poll_task_status($task_id) {
        $api_url = $this->api_base_url . '/task-status/' . $task_id;

        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));

        if (is_wp_error($response)) {
            return array('success' => false, 'error' => 'Failed to fetch task status.');
        }

        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        return $data;
    }

    /**
     * Handle AJAX update request with task status polling.
     */
    public function handle_update_request() {
        // Verify nonce
        check_ajax_referer('smartlink_update_action', 'nonce');

        // Get post ID
        $post_id = isset($_POST['post_id']) ? intval($_POST['post_id']) : 0;

        if (!$post_id) {
            wp_send_json_error(array('error' => 'Invalid post ID.'));
        }

        // Call the Cloud Run API to start the update
        $api_url = $this->api_base_url . '/update-post/' . $post_id;
        $response = wp_remote_post($api_url, array('timeout' => 10));

        if (is_wp_error($response)) {
            wp_send_json_error(array('error' => 'Failed to start update.'));
        }

        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);

        if (!isset($data['task_id'])) {
            wp_send_json_error(array('error' => 'Task ID not returned.'));
        }

        $task_id = $data['task_id'];

        // Poll the task status endpoint
        $status = $this->poll_task_status($task_id);

        if (!$status['success']) {
            wp_send_json_error(array('error' => $status['error']));
        }

        wp_send_json_success($status);
    }
}

// Initialize the plugin
new SmartLinkUpdater();
