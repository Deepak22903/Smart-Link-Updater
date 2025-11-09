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
        
        // Register custom cron schedules
        add_filter('cron_schedules', array($this, 'add_cron_schedules'));
        
        // Register cron action for scheduled updates
        add_action('slu_scheduled_update', array($this, 'run_scheduled_update'));
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
        
        // Add Analytics submenu
        add_submenu_page(
            'smartlink-updater',            // Parent slug
            'Analytics',                    // Page title
            'Analytics',                    // Menu title
            'edit_posts',                   // Capability
            'smartlink-analytics',          // Menu slug
            array($this, 'render_analytics_page') // Callback
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
            add_action('admin_head', array($this, 'print_config_script'), 99); // Load config before main script
            add_action('admin_footer', array($this, 'print_admin_page_script'));
        }
        
        // Load on analytics page
        if ('smartlink_page_smartlink-analytics' === $hook) {
            // Enqueue Chart.js library
            wp_enqueue_script('chart-js', 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js', array(), '4.4.0', true);
            add_action('admin_head', array($this, 'print_analytics_css'));
            add_action('admin_head', array($this, 'print_config_script'), 99);
            add_action('admin_footer', array($this, 'print_analytics_script'));
        }
    }
    
    /**
     * Print configuration script
     */
    public function print_config_script() {
        ?>
        <script type="text/javascript">
        // Pass REST API URLs to JavaScript (server-side proxy)
        window.SmartLinkConfig = {
            restUrl: '<?php echo esc_url(rest_url('smartlink/v1')); ?>',
            nonce: '<?php echo wp_create_nonce('wp_rest'); ?>',
            pollInterval: 2000 // 2 seconds
        };
        console.log('SmartLinkConfig initialized:', window.SmartLinkConfig);
        </script>
        <?php
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

        /* Cron Status Banner Styles */
        .cron-status-enabled {
            background: linear-gradient(135deg, #a8e6cf 0%, #3fc380 100%) !important;
            color: #1e4d2b !important;
        }
        
        .cron-status-enabled #cron-icon {
            color: #1e4d2b !important;
        }
        
        .cron-status-disabled {
            background: linear-gradient(135deg, #ffb199 0%, #ff6b6b 100%) !important;
            color: #4a0000 !important;
        }
        
        .cron-status-disabled #cron-icon {
            color: #4a0000 !important;
        }

        /* Search and Filter Styles */
        #search-posts:focus,
        #filter-extractor:focus,
        #filter-health:focus,
        #filter-status:focus {
            border-color: #667eea !important;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        #apply-filters:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        #clear-filters:hover {
            background: #f5f5f5;
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
            overflow-x: auto;
            overflow-y: visible;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        .smartlink-posts-table {
            margin: 0;
            border-collapse: separate;
            border-spacing: 0;
            min-width: 1200px;
            width: 100%;
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
            transition: background 0.2s ease, box-shadow 0.2s ease;
        }

        .smartlink-posts-table tbody tr:hover {
            background: linear-gradient(135deg, #f8f9ff 0%, #fdf4ff 100%);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
        }

        .column-post-id {
            width: 80px;
        }

        .column-extractor {
            width: 150px;
        }

        .column-status {
            width: 200px;
        }

        .column-progress {
            width: 150px;
        }
        
        .column-last-updated {
            width: 130px;
        }

        .column-actions {
            width: 150px;
            white-space: nowrap;
            position: relative;
        }

        .actions-cell {
            white-space: nowrap;
            position: relative;
        }
        
        .action-menu .menu-item:hover {
            background: #f5f5f5;
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
        
        .actions-cell .button {
            margin-right: 4px;
        }
        
        .actions-cell .button:last-child {
            margin-right: 0;
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
                loadWordPressSites();
                attachEventListeners();
                loadCronStatus();
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
                
                // Cron management
                console.log('Attaching cron event listeners...');
                console.log('Configure button exists:', $('#configure-cron-btn').length);
                console.log('Toggle button exists:', $('#toggle-cron-btn').length);
                console.log('Save button exists:', $('#save-cron-btn').length);
                
                $('#view-cron-history-btn').on('click', openCronHistory);
                $('#configure-cron-btn').on('click', openCronModal);
                $('#toggle-cron-btn').on('click', toggleCron);
                $('#save-cron-btn').on('click', saveCronSettings);
                $('#refresh-cron-history').on('click', loadCronHistory);
                
                // Search and filter
                $('#apply-filters').on('click', applyFilters);
                $('#clear-filters').on('click', clearFilters);
                $('#search-posts').on('keypress', function(e) {
                    if (e.which === 13) { // Enter key
                        applyFilters();
                    }
                });
                
                // Post configuration
                $('#add-new-config-btn').on('click', openAddConfigModal);
                $('#save-config-btn').on('click', savePostConfig);
                $('#add-url-btn').on('click', addSourceUrlField);
                $('input[name="extractor-mode"]').on('change', toggleExtractorMode);
                
                // Delegate checkbox change event
                $(document).on('change', '.post-checkbox', updateSelectedCount);
                $(document).on('click', '.view-logs-btn', viewLogs);
                $(document).on('click', '.single-update-btn', singleUpdate);
                $(document).on('click', '.edit-config-btn', openEditConfigModal);
                $(document).on('click', '.delete-config-btn', deletePostConfig);
                $(document).on('click', '.remove-url-btn', removeSourceUrlField);
                
                // Action menu toggle
                $(document).on('click', '.action-menu-btn', function(e) {
                    e.stopPropagation();
                    const postId = $(this).data('post-id');
                    const menu = $('.action-menu[data-post-id="' + postId + '"]');
                    
                    // Close other menus
                    $('.action-menu').not(menu).hide();
                    
                    // Toggle this menu
                    menu.toggle();
                });
                
                // Close menu when clicking outside
                $(document).on('click', function() {
                    $('.action-menu').hide();
                });
                
                // Prevent menu from closing when clicking inside
                $(document).on('click', '.action-menu', function(e) {
                    e.stopPropagation();
                });
                
                // Handle menu item clicks
                $(document).on('click', '.action-menu .menu-item', function() {
                    $('.action-menu').hide();
                });
            }
            
            // ========== CRON MANAGEMENT ==========
            
            function loadCronStatus() {
                console.log('loadCronStatus called');
                console.log('Cron status URL:', config.restUrl + '/cron/status');
                $.ajax({
                    url: config.restUrl + '/cron/status',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        console.log('Cron status response:', response);
                        // REST API returns data directly, not wrapped in {success: true, data: ...}
                        updateCronStatusDisplay(response);
                    },
                    error: function(xhr, status, error) {
                        console.error('Failed to load cron status:', status, error);
                        console.error('Response:', xhr.responseText);
                        console.error('Status code:', xhr.status);
                    }
                });
            }
            
            function updateCronStatusDisplay(data) {
                const banner = $('#cron-status-banner');
                const statusText = $('#cron-status-text');
                const scheduleDisplay = $('#cron-schedule-display');
                const postsDisplay = $('#cron-posts-display');
                const lastRunDisplay = $('#cron-last-run-display');
                const nextRunDisplay = $('#cron-next-run-display');
                const toggleBtn = $('#toggle-cron-btn');
                const toggleText = $('#toggle-cron-text');
                
                // Show/hide info sections
                const infoSections = ['#cron-schedule-info', '#cron-posts-info', '#cron-lastrun-info', '#cron-nextrun-info'];
                
                if (data.enabled) {
                    // Enabled - Green theme
                    banner.removeClass('cron-status-disabled').addClass('cron-status-enabled');
                    statusText.text('Enabled').css('color', '#1e4d2b').css('font-weight', '600');
                    scheduleDisplay.text(data.schedule_label || data.schedule || '-');
                    postsDisplay.text(data.total_posts || '0');
                    lastRunDisplay.text(data.last_run || 'Never');
                    nextRunDisplay.text(data.next_run || '-');
                    toggleText.text('Disable');
                    toggleBtn.removeClass('button-secondary').addClass('button-primary');
                    
                    // Show all info sections
                    infoSections.forEach(selector => $(selector).show());
                } else {
                    // Disabled - Red theme
                    banner.removeClass('cron-status-enabled').addClass('cron-status-disabled');
                    statusText.text('Disabled').css('color', '#4a0000').css('font-weight', '600');
                    toggleText.text('Enable');
                    toggleBtn.removeClass('button-primary').addClass('button-secondary');
                    
                    // Hide info sections when disabled
                    infoSections.forEach(selector => $(selector).hide());
                }
            }
            
            function openCronModal() {
                console.log('openCronModal called');
                $.ajax({
                    url: config.restUrl + '/cron/settings',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(settings) {
                        console.log('Cron settings loaded:', settings);
                        $('#cron-enabled').prop('checked', settings.enabled);
                        $('#cron-schedule').val(settings.schedule);
                        $('#cron-modal').fadeIn();
                    },
                    error: function(xhr) {
                        console.error('Failed to load cron settings:', xhr);
                        alert('Failed to load cron settings: ' + xhr.responseText);
                    }
                });
            }
            
            function toggleCron() {
                console.log('toggleCron called');
                $.ajax({
                    url: config.restUrl + '/cron/settings',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(settings) {
                        settings.enabled = !settings.enabled;
                        saveCronSettingsData(settings);
                    },
                    error: function(xhr) {
                        alert('Failed to toggle cron: ' + xhr.responseText);
                    }
                });
            }
            
            function saveCronSettings() {
                const settings = {
                    enabled: $('#cron-enabled').is(':checked'),
                    schedule: $('#cron-schedule').val()
                };
                
                saveCronSettingsData(settings);
            }
            
            function saveCronSettingsData(settings) {
                $.ajax({
                    url: config.restUrl + '/cron/settings',
                    method: 'POST',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                        xhr.setRequestHeader('Content-Type', 'application/json');
                    },
                    data: JSON.stringify(settings),
                    success: function(response) {
                        console.log('Save response:', response);
                        $('#cron-modal').fadeOut();
                        loadCronStatus();
                        alert('Cron settings saved successfully!');
                    },
                    error: function(xhr) {
                        alert('Failed to save cron settings: ' + xhr.responseText);
                    }
                });
            }
            
            function openCronHistory() {
                $('#cron-history-modal').fadeIn();
                loadCronHistory();
            }
            
            function loadCronHistory() {
                const contentDiv = $('#cron-history-content');
                contentDiv.html('<div style="text-align: center; padding: 40px;"><span class="spinner is-active" style="float: none;"></span><p>Loading history...</p></div>');
                
                $.ajax({
                    url: config.restUrl + '/cron/history',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(history) {
                        renderCronHistory(history);
                    },
                    error: function(xhr) {
                        contentDiv.html('<div style="text-align: center; padding: 40px; color: #e74c3c;"><span class="dashicons dashicons-warning" style="font-size: 48px;"></span><p>Failed to load history</p></div>');
                    }
                });
            }
            
            function renderCronHistory(history) {
                const contentDiv = $('#cron-history-content');
                
                if (!history || history.length === 0) {
                    contentDiv.html('<div style="text-align: center; padding: 40px; color: #666;"><span class="dashicons dashicons-clock" style="font-size: 48px; opacity: 0.3;"></span><p>No scheduled update history yet</p></div>');
                    return;
                }
                
                let html = '<div style="display: flex; flex-direction: column; gap: 12px;">';
                
                history.forEach(function(entry) {
                    const statusColors = {
                        'success': { bg: '#d4edda', border: '#27ae60', text: '#155724', icon: 'yes-alt' },
                        'error': { bg: '#f8d7da', border: '#e74c3c', text: '#721c24', icon: 'dismiss' },
                        'warning': { bg: '#fff3cd', border: '#ffc107', text: '#856404', icon: 'warning' }
                    };
                    
                    const style = statusColors[entry.status] || statusColors['warning'];
                    
                    html += '<div style="background: ' + style.bg + '; border-left: 4px solid ' + style.border + '; padding: 15px 20px; border-radius: 8px;">';
                    html += '<div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">';
                    html += '<div style="flex: 1;">';
                    html += '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">';
                    html += '<span class="dashicons dashicons-' + style.icon + '" style="color: ' + style.text + ';"></span>';
                    html += '<strong style="color: ' + style.text + '; text-transform: uppercase; font-size: 12px;">' + entry.status + '</strong>';
                    html += '</div>';
                    html += '<p style="margin: 0 0 8px 0; color: ' + style.text + ';">' + entry.message + '</p>';
                    html += '<div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px; color: #666;">';
                    html += '<div><strong>Posts:</strong> ' + entry.post_count + '</div>';
                    if (entry.request_id) {
                        html += '<div><strong>Request ID:</strong> <code style="background: rgba(0,0,0,0.05); padding: 2px 6px; border-radius: 3px; font-size: 11px;">' + entry.request_id + '</code></div>';
                    }
                    html += '</div>';
                    html += '</div>';
                    html += '<div style="text-align: right; min-width: 140px;">';
                    html += '<div style="font-size: 13px; color: #666;">' + entry.formatted_time + '</div>';
                    html += '<div style="font-size: 12px; color: #999; margin-top: 4px;">' + entry.time_ago + '</div>';
                    html += '</div>';
                    html += '</div>';
                    html += '</div>';
                });
                
                html += '</div>';
                contentDiv.html(html);
            }
            
            // ========== SEARCH AND FILTER ==========
            
            let activeFilters = {
                search: '',
                extractor: '',
                health: '',
                status: ''
            };
            
            function applyFilters() {
                activeFilters.search = $('#search-posts').val().toLowerCase().trim();
                activeFilters.extractor = $('#filter-extractor').val();
                activeFilters.health = $('#filter-health').val();
                activeFilters.status = $('#filter-status').val();
                
                const filteredPosts = postsData.filter(post => {
                    // Search filter
                    if (activeFilters.search) {
                        const titleMatch = post.title.toLowerCase().includes(activeFilters.search);
                        const idMatch = post.post_id.toString().includes(activeFilters.search);
                        if (!titleMatch && !idMatch) return false;
                    }
                    
                    // Extractor filter
                    if (activeFilters.extractor && post.extractor_type !== activeFilters.extractor) {
                        return false;
                    }
                    
                    // Health filter
                    if (activeFilters.health && post.health_status !== activeFilters.health) {
                        return false;
                    }
                    
                    // Status filter
                    if (activeFilters.status && post.status !== activeFilters.status) {
                        return false;
                    }
                    
                    return true;
                });
                
                renderPostsTable(filteredPosts);
                updateActiveFiltersDisplay();
            }
            
            function clearFilters() {
                $('#search-posts').val('');
                $('#filter-extractor').val('');
                $('#filter-health').val('');
                $('#filter-status').val('');
                
                activeFilters = {
                    search: '',
                    extractor: '',
                    health: '',
                    status: ''
                };
                
                renderPostsTable(postsData);
                updateActiveFiltersDisplay();
            }
            
            function updateActiveFiltersDisplay() {
                const activeFiltersDiv = $('#active-filters');
                const filterTagsDiv = $('#filter-tags');
                filterTagsDiv.empty();
                
                let hasFilters = false;
                
                if (activeFilters.search) {
                    hasFilters = true;
                    filterTagsDiv.append(createFilterTag('Search', activeFilters.search, 'search'));
                }
                
                if (activeFilters.extractor) {
                    hasFilters = true;
                    const label = $('#filter-extractor option:selected').text();
                    filterTagsDiv.append(createFilterTag('Extractor', label, 'extractor'));
                }
                
                if (activeFilters.health) {
                    hasFilters = true;
                    const label = $('#filter-health option:selected').text();
                    filterTagsDiv.append(createFilterTag('Health', label, 'health'));
                }
                
                if (activeFilters.status) {
                    hasFilters = true;
                    const label = $('#filter-status option:selected').text();
                    filterTagsDiv.append(createFilterTag('Status', label, 'status'));
                }
                
                if (hasFilters) {
                    activeFiltersDiv.show();
                } else {
                    activeFiltersDiv.hide();
                }
            }
            
            function createFilterTag(label, value, type) {
                const tag = $('<span>').css({
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'color': 'white',
                    'padding': '4px 12px',
                    'border-radius': '20px',
                    'font-size': '12px',
                    'display': 'inline-flex',
                    'align-items': 'center',
                    'gap': '6px'
                }).html(`<strong>${label}:</strong> ${value}`);
                
                const removeBtn = $('<span>').css({
                    'cursor': 'pointer',
                    'font-weight': 'bold',
                    'margin-left': '4px'
                }).text('×').on('click', function() {
                    if (type === 'search') {
                        $('#search-posts').val('');
                    } else {
                        $(`#filter-${type}`).val('');
                    }
                    applyFilters();
                });
                
                tag.append(removeBtn);
                return tag;
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

                        // Normalize title field so filtering/search consistently uses `post.title`
                        postsData = postsData.map(function(p) {
                            // prefer existing `title` string
                            if (!p.title) {
                                if (typeof p.post_title === 'string') {
                                    p.title = p.post_title;
                                } else if (p.post_title && p.post_title.rendered) {
                                    p.title = p.post_title.rendered;
                                } else if (p.title && typeof p.title === 'object' && p.title.rendered) {
                                    p.title = p.title.rendered;
                                } else if (p.title && typeof p.title === 'string') {
                                    // already a string
                                } else {
                                    p.title = 'Post ' + (p.post_id || '');
                                }
                            }
                            return p;
                        });

                        renderPostsTable(postsData);
                    },
                    error: function(xhr) {
                        showToast('Failed to load posts: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            function loadWordPressSites() {
                $.ajax({
                    url: config.restUrl + '/sites',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        const sites = response.sites || {};
                        
                        // Store sites globally for use in other functions
                        window.availableSites = Object.keys(sites).map(function(key) {
                            return {
                                site_key: key,
                                display_name: sites[key].base_url || key
                            };
                        });
                        
                        const select = $('#target-site-select');
                        
                        // Remove old dynamic options (keep This Site and All Sites)
                        select.find('option').not('[value="this"], [value="all"]').remove();
                        
                        // Add individual site options
                        Object.keys(sites).forEach(function(siteKey) {
                            const site = sites[siteKey];
                            const option = $('<option>')
                                .val(siteKey)
                                .text(site.base_url || siteKey);
                            select.append(option);
                        });
                    },
                    error: function(xhr) {
                        console.warn('Failed to load WordPress sites:', xhr.responseJSON?.message || 'Unknown error');
                    }
                });
            }
            
            function loadSitePostIdFields(existingSitePostIds) {
                const $container = $('#site-post-ids-fields');
                $container.empty();
                
                if (!window.availableSites || window.availableSites.length === 0) {
                    $container.html('<p style="color: #999; font-style: italic; margin: 0;">Loading sites...</p>');
                    return;
                }
                
                existingSitePostIds = existingSitePostIds || {};
                
                window.availableSites.forEach(function(site) {
                    const value = existingSitePostIds[site.site_key] || '';
                    $container.append(`
                        <div style="display: flex; align-items: center; margin-bottom: 10px;">
                            <label style="flex: 0 0 200px; font-weight: 600; color: #555;">${escapeHtml(site.display_name)}:</label>
                            <input type="number" 
                                   class="site-post-id-input" 
                                   data-site-key="${escapeHtml(site.site_key)}" 
                                   value="${value}" 
                                   placeholder="Post ID on ${escapeHtml(site.display_name)}" 
                                   style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                        </div>
                    `);
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
                    
                    // Post ID (or content_slug if available)
                    const idCell = $('<td>').css('font-weight', '600');
                    if (post.content_slug) {
                        idCell.html(
                            `<span style="color: #667eea; font-weight: 600;" title="Content Slug">${escapeHtml(post.content_slug)}</span><br>` +
                            `<span style="font-size: 11px; color: #999;">ID: ${post.post_id}</span>`
                        );
                    } else {
                        idCell.text('#' + post.post_id);
                    }
                    row.append(idCell);

                    // Post (title/name)
                    row.append($('<td>').text(post.title || ('Post ' + post.post_id)));
                    
                    // Extractor
                    row.append($('<td>').html(`<span style="background: #e8e8e8; padding: 4px 10px; border-radius: 4px; font-size: 12px;">${post.extractor || 'default'}</span>`));
                    
                    // Status (with badge and description)
                    const statusHtml = getStatusBadgeWithDescription(post);
                    row.append($('<td>').addClass('status-cell').html(statusHtml));
                    
                    // Progress (with percentage and bar)
                    let percent = 0;
                    if (typeof post.progress_percent === 'number') {
                        percent = Math.min(100, Math.max(0, Math.round(post.progress_percent)));
                    } else if (typeof post.progress === 'number') {
                        // support 0..1 or 0..100 progress values
                        if (post.progress <= 1) percent = Math.round(post.progress * 100);
                        else percent = Math.round(post.progress);
                    } else if (post.completed && post.total) {
                        percent = Math.round((post.completed / post.total) * 100);
                    } else if (post.status) {
                        const st = String(post.status).toLowerCase();
                        if (st === 'done' || st === 'completed' || st === 'success') percent = 100;
                    }

                    percent = Math.min(100, Math.max(0, percent || 0));

                    const progressHtml = `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="progress-bar small" style="flex: 1; height: 8px; background: #e8e8e8; border-radius: 4px; overflow: hidden;">
                                <div class="progress-fill" style="width: ${percent}%; height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s;"></div>
                            </div>
                            <span style="font-weight: 600; font-size: 13px; min-width: 45px;">${percent}%</span>
                        </div>
                    `;
                    row.append($('<td>').addClass('progress-cell').html(progressHtml));
                    
                    // Last Updated
                    const lastUpdated = post.last_updated ? formatTimeAgo(post.last_updated) : '-';
                    row.append($('<td>').text(lastUpdated).css({'color': '#666', 'font-size': '13px'}));
                    
                    // Actions (Update button + three-dot menu)
                    const actionsCell = $('<td>').addClass('actions-cell').css({'text-align': 'center', 'position': 'relative'});
                    
                    // Update button (standalone)
                    const updateBtn = $('<button>').addClass('button button-primary button-small single-update-btn').attr('data-post-id', post.post_id).html(
                        '<span class="dashicons dashicons-update" style="font-size: 13px; line-height: 1.4;"></span> Update'
                    ).css({
                        'margin-right': '8px',
                        'padding': '6px 12px',
                        'font-size': '12px'
                    });
                    
                    // Three-dot menu button
                    const menuBtn = $('<button>').addClass('action-menu-btn').attr('data-post-id', post.post_id).html('⋮').css({
                        'background': 'none',
                        'border': 'none',
                        'font-size': '20px',
                        'cursor': 'pointer',
                        'padding': '5px 10px',
                        'color': '#666'
                    });
                    
                    // Menu dropdown (only Edit and Delete)
                    const menu = $('<div>').addClass('action-menu').attr('data-post-id', post.post_id).css({
                        'display': 'none',
                        'position': 'absolute',
                        'right': '10px',
                        'background': 'white',
                        'border': '1px solid #ddd',
                        'border-radius': '8px',
                        'box-shadow': '0 4px 12px rgba(0,0,0,0.15)',
                        'z-index': '1000',
                        'min-width': '120px'
                    }).html(`
                        <div class="menu-item view-logs-btn" data-post-id="${post.post_id}" style="padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;">
                            <span class="dashicons dashicons-media-text" style="font-size: 14px;"></span> View Logs
                        </div>
                        <div class="menu-item edit-config-btn" data-post-id="${post.post_id}" style="padding: 10px 15px; cursor: pointer; border-bottom: 1px solid #f0f0f0;">
                            <span class="dashicons dashicons-edit" style="font-size: 14px;"></span> Edit
                        </div>
                        <div class="menu-item delete-config-btn" data-post-id="${post.post_id}" style="padding: 10px 15px; cursor: pointer; color: #dc3232;">
                            <span class="dashicons dashicons-trash" style="font-size: 14px;"></span> Delete
                        </div>
                    `);
                    
                    actionsCell.append(updateBtn).append(menuBtn).append(menu);
                    row.append(actionsCell);
                    
                    tbody.append(row);
                });
            }
            
            function getStatusBadgeWithDescription(post) {
                const status = post.status || 'idle';
                let badge, description;
                
                if (status === 'updated' || status === 'completed') {
                    badge = '<span style="display: inline-flex; align-items: center; gap: 5px; background: #10b981; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;"><span>✓</span> Updated</span>';
                    description = '<div style="font-size: 12px; color: #666; margin-top: 4px;">Added 1 links</div>';
                } else if (status === 'up_to_date') {
                    badge = '<span style="display: inline-flex; align-items: center; gap: 5px; background: #6366f1; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;"><span>⏰</span> Up to Date</span>';
                    description = '<div style="font-size: 12px; color: #666; margin-top: 4px;">No new links found</div>';
                } else {
                    badge = '<span style="display: inline-flex; align-items: center; gap: 5px; background: #9ca3af; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;">Idle</span>';
                    description = '';
                }
                
                return badge + description;
            }
            
            function formatTimeAgo(timestamp) {
                if (!timestamp) return '-';
                
                const now = new Date();
                const past = new Date(timestamp);
                const diffMs = now - past;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);
                
                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return diffMins + ' mins ago';
                if (diffHours < 24) return diffHours + ' hours ago';
                if (diffDays < 30) return diffDays + ' days ago';
                return past.toLocaleDateString();
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
                    
                    // Update progress bar AND percentage text
                    const progressWidth = postState.progress || 0;
                    const progressCell = row.find('.progress-cell');
                    progressCell.find('.progress-fill').css('width', progressWidth + '%');
                    progressCell.find('span').text(Math.round(progressWidth) + '%');
                    
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
            
            // ========== POST CONFIGURATION ==========
            
            function openAddConfigModal() {
                $('#config-mode').val('add');
                $('#config-modal-title').text('Add Post Configuration');
                $('#save-config-text').text('Save Configuration');
                $('#post-config-form')[0].reset();
                $('#config-post-id').prop('disabled', false);
                $('#config-content-slug').val('');
                
                // Reset to single URL
                $('#source-urls-container').html(`
                    <div class="source-url-row" style="display: flex; gap: 8px; margin-bottom: 8px;">
                        <input type="url" class="source-url-input smartlink-input" placeholder="https://example.com/links/" required
                               style="flex: 1; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                        <button type="button" class="button remove-url-btn" style="display: none;">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                `);
                
                loadSitePostIdFields();
                $('#post-config-modal').fadeIn();
            }
            
            function openEditConfigModal(e) {
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                $('#config-mode').val('edit');
                $('#config-modal-title').text('Edit Post Configuration');
                $('#save-config-text').text('Update Configuration');
                $('#config-post-id').val(postId).prop('disabled', true);
                
                // Load existing configuration
                showToast('Loading configuration...', 'info');
                
                $.ajax({
                    url: config.restUrl + '/config/post/' + postId,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(postConfig) {
                        console.log('Loaded config:', postConfig);
                        
                        // Populate content slug
                        $('#config-content-slug').val(postConfig.content_slug || '');
                        
                        // Populate source URLs
                        const sourceUrls = postConfig.source_urls || [];
                        $('#source-urls-container').empty();
                        
                        sourceUrls.forEach(function(url, index) {
                            const showRemove = sourceUrls.length > 1;
                            $('#source-urls-container').append(`
                                <div class="source-url-row" style="display: flex; gap: 8px; margin-bottom: 8px;">
                                    <input type="url" class="source-url-input smartlink-input" value="${url}" required
                                           style="flex: 1; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                    <button type="button" class="button remove-url-btn" style="${showRemove ? '' : 'display: none;'}">
                                        <span class="dashicons dashicons-no-alt"></span>
                                    </button>
                                </div>
                            `);
                        });
                        
                        // Set timezone
                        $('#config-timezone').val(postConfig.timezone || 'Asia/Kolkata');
                        
                        // Set extractor mode
                        const extractorMap = postConfig.extractor_map || {};
                        const hasExtractorMap = Object.keys(extractorMap).length > 0;
                        
                        if (hasExtractorMap) {
                            $('input[name="extractor-mode"][value="per-url"]').prop('checked', true);
                            toggleExtractorMode();
                            updateExtractorMapping();
                            
                            // Populate extractor map
                            Object.keys(extractorMap).forEach(function(url) {
                                $(`select[data-url="${url}"]`).val(extractorMap[url]);
                            });
                        } else {
                            $('input[name="extractor-mode"][value="auto"]').prop('checked', true);
                            toggleExtractorMode();
                        }
                        
                        // Load site post IDs
                        loadSitePostIdFields(postConfig.site_post_ids);
                        
                        $('#post-config-modal').fadeIn();
                    },
                    error: function(xhr) {
                        showToast('Failed to load configuration: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            function savePostConfig() {
                const mode = $('#config-mode').val();
                const postId = parseInt($('#config-post-id').val());
                const contentSlug = $('#config-content-slug').val().trim();
                
                // Collect site_post_ids
                const sitePostIds = {};
                let hasSiteIds = false;
                $('.site-post-id-input').each(function() {
                    const siteKey = $(this).data('site-key');
                    const sitePostId = parseInt($(this).val());
                    if (sitePostId && sitePostId > 0) {
                        sitePostIds[siteKey] = sitePostId;
                        hasSiteIds = true;
                    }
                });
                
                // Validation: Need either legacy post_id or at least one site-specific post ID
                if (!postId && !hasSiteIds) {
                    showToast('Please enter either a legacy post ID or at least one site-specific post ID', 'error');
                    return;
                }
                
                // Collect source URLs
                const sourceUrls = [];
                $('.source-url-input').each(function() {
                    const url = $(this).val().trim();
                    if (url) {
                        sourceUrls.push(url);
                    }
                });
                
                if (sourceUrls.length === 0) {
                    showToast('Please add at least one source URL', 'error');
                    return;
                }
                
                // Build configuration object
                const configData = {
                    post_id: postId || (hasSiteIds ? Object.values(sitePostIds)[0] : 0), // Use first site ID as fallback
                    source_urls: sourceUrls,
                    timezone: $('#config-timezone').val()
                };
                
                // Add optional fields
                if (contentSlug) {
                    configData.content_slug = contentSlug;
                }
                if (hasSiteIds) {
                    configData.site_post_ids = sitePostIds;
                }
                
                // Handle extractor configuration - only save extractor_map if per-url mode
                const extractorMode = $('input[name="extractor-mode"]:checked').val();
                
                if (extractorMode === 'per-url') {
                    const extractorMap = {};
                    $('.extractor-url-mapping').each(function() {
                        const url = $(this).data('url');
                        const extractor = $(this).val();
                        if (extractor) {  // Only add if not empty (not auto-detect)
                            extractorMap[url] = extractor;
                        }
                    });
                    if (Object.keys(extractorMap).length > 0) {
                        configData.extractor_map = extractorMap;
                    }
                }
                // If auto mode, don't send any extractor config - backend will auto-detect

                
                // Disable button and show loading
                const $btn = $('#save-config-btn');
                $btn.prop('disabled', true).html('<span class="spinner is-active" style="float: none;"></span> Saving...');
                
                // Send to API
                const method = mode === 'add' ? 'POST' : 'PUT';
                const url = mode === 'add' 
                    ? config.restUrl + '/config/post'
                    : config.restUrl + '/config/post/' + postId;
                
                $.ajax({
                    url: url,
                    method: method,
                    contentType: 'application/json',
                    data: JSON.stringify(configData),
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        showToast(mode === 'add' ? 'Configuration added successfully!' : 'Configuration updated successfully!', 'success');
                        $('#post-config-modal').fadeOut();
                        loadPosts(); // Refresh posts table
                    },
                    error: function(xhr) {
                        showToast('Failed to save configuration: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    },
                    complete: function() {
                        $btn.prop('disabled', false).html(
                            '<span class="dashicons dashicons-yes"></span><span id="save-config-text">' + 
                            (mode === 'add' ? 'Save Configuration' : 'Update Configuration') + '</span>'
                        );
                    }
                });
            }
            
            function deletePostConfig(e) {
                const postId = $(e.currentTarget).data('post-id');
                
                if (!confirm('Are you sure you want to delete the configuration for Post ID ' + postId + '? This action cannot be undone.')) {
                    return;
                }
                
                const $btn = $(e.currentTarget);
                $btn.prop('disabled', true);
                
                showToast('Deleting configuration...', 'info');
                
                $.ajax({
                    url: config.restUrl + '/config/post/' + postId,
                    method: 'DELETE',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        showToast('Configuration deleted successfully!', 'success');
                        loadPosts(); // Refresh the posts table
                    },
                    error: function(xhr) {
                        showToast('Failed to delete configuration: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                        $btn.prop('disabled', false);
                    }
                });
            }
            
            function addSourceUrlField() {
                const newField = $(`
                    <div class="source-url-row" style="display: flex; gap: 8px; margin-bottom: 8px;">
                        <input type="url" class="source-url-input smartlink-input" placeholder="https://example.com/links/" required
                               style="flex: 1; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                        <button type="button" class="button remove-url-btn">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                `);
                
                $('#source-urls-container').append(newField);
                
                // Show remove buttons if we have multiple URLs
                if ($('.source-url-row').length > 1) {
                    $('.remove-url-btn').show();
                }
                
                // Update extractor mapping if in per-url mode
                const extractorMode = $('input[name="extractor-mode"]:checked').val();
                if (extractorMode === 'per-url') {
                    updateExtractorMapping();
                }
            }
            
            function removeSourceUrlField(e) {
                $(e.currentTarget).closest('.source-url-row').remove();
                
                // Hide remove buttons if only one URL left
                if ($('.source-url-row').length === 1) {
                    $('.remove-url-btn').hide();
                }
                
                // Update extractor mapping if in per-url mode
                const extractorMode = $('input[name="extractor-mode"]:checked').val();
                if (extractorMode === 'per-url') {
                    updateExtractorMapping();
                }
            }
            
            function toggleExtractorMode() {
                const mode = $('input[name="extractor-mode"]:checked').val();
                
                $('#per-url-extractor-config').hide();
                
                if (mode === 'per-url') {
                    $('#per-url-extractor-config').show();
                    updateExtractorMapping();
                }
            }
            
            function updateExtractorMapping() {
                const container = $('#extractor-mapping-container');
                container.empty();
                
                $('.source-url-input').each(function(index) {
                    const url = $(this).val().trim();
                    if (!url) return;
                    
                    container.append(`
                        <div style="margin-bottom: 12px; padding: 12px; background: #f9f9f9; border-radius: 8px;">
                            <label style="display: block; margin-bottom: 6px; font-weight: 600; font-size: 13px; color: #555;">
                                URL ${index + 1}: ${url.length > 50 ? url.substring(0, 50) + '...' : url}
                            </label>
                            <select class="extractor-url-mapping smartlink-select" data-url="${url}" style="width: 100%; padding: 8px; border: 2px solid #ddd; border-radius: 6px;">
                                <option value="">Auto-detect</option>
                                <option value="simplegameguide">Simple Game Guide</option>
                                <option value="mosttechs">Most Techs</option>
                                <option value="crazyashwin">Crazy Ashwin</option>
                                <option value="techyhigher">Techy Higher</option>
                                <option value="default">Default Extractor</option>
                            </select>
                        </div>
                    `);
                });
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
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 20px 0;">
                <h1 style="margin: 0;">
                    <span class="dashicons dashicons-update"></span>
                    SmartLink Updater Dashboard
                </h1>
                <button type="button" id="add-new-config-btn" class="button button-primary" style="font-size: 16px; padding: 10px 20px; height: auto;">
                    <span class="dashicons dashicons-plus-alt"></span>
                    Add New Config
                </button>
            </div>
            
            <!-- Notification Toast -->
            <div id="smartlink-toast" class="smartlink-toast" style="display: none;"></div>
            
            <!-- Cron Schedule Status -->
            <div id="cron-status-banner" class="cron-status-disabled" style="padding: 20px 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; gap: 15px; flex: 1;">
                    <span class="dashicons dashicons-clock" id="cron-icon" style="font-size: 32px; width: 32px; height: 32px;"></span>
                    <div>
                        <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">Scheduled Updates</h3>
                        <div id="cron-status-info" style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 14px;">
                            <div><strong>Status:</strong> <span id="cron-status-text">Loading...</span></div>
                            <div id="cron-schedule-info" style="display: none;"><strong>Schedule:</strong> <span id="cron-schedule-display">-</span></div>
                            <div id="cron-posts-info" style="display: none;"><strong>Posts:</strong> <span id="cron-posts-display">0</span></div>
                            <div id="cron-lastrun-info" style="display: none;"><strong>Last Run:</strong> <span id="cron-last-run-display">Never</span></div>
                            <div id="cron-nextrun-info" style="display: none;"><strong>Next Run:</strong> <span id="cron-next-run-display">-</span></div>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <button type="button" id="view-cron-history-btn" class="button" style="background: white; color: #2d3436; border: 2px solid rgba(0,0,0,0.2); font-weight: 600; transition: all 0.2s;">
                        <span class="dashicons dashicons-backup"></span>
                        History
                    </button>
                    <button type="button" id="configure-cron-btn" class="button" style="background: white; color: #2d3436; border: 2px solid rgba(0,0,0,0.2); font-weight: 600; transition: all 0.2s;">
                        <span class="dashicons dashicons-admin-generic"></span>
                        Configure
                    </button>
                    <button type="button" id="toggle-cron-btn" class="button button-primary" style="min-width: 140px; font-weight: 600; transition: all 0.2s;">
                        <span class="dashicons dashicons-controls-play"></span>
                        <span id="toggle-cron-text">Enable</span>
                    </button>
                </div>
            </div>
            
            <!-- Cron Configuration Modal -->
            <div id="cron-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 600px;">
                    <div class="smartlink-modal-header">
                        <h2>
                            <span class="dashicons dashicons-clock"></span>
                            Configure Scheduled Updates
                        </h2>
                        <button type="button" class="close-modal" onclick="document.getElementById('cron-modal').style.display='none'">×</button>
                    </div>
                    <div class="smartlink-modal-body">
                        <div style="margin-bottom: 20px;">
                            <label style="display: flex; align-items: center; gap: 8px; font-weight: 600; color: #333; cursor: pointer;">
                                <input type="checkbox" id="cron-enabled" style="width: 18px; height: 18px;">
                                Enable automatic scheduled updates
                            </label>
                            <p style="color: #666; font-size: 13px; margin: 8px 0 0 26px;">
                                When enabled, all configured posts will be automatically updated on the schedule below
                            </p>
                        </div>
                        
                        <div style="margin-bottom: 20px;">
                            <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                <span class="dashicons dashicons-clock" style="font-size: 16px; vertical-align: middle;"></span>
                                Update Frequency
                            </label>
                            <select id="cron-schedule" class="smartlink-select" style="width: 100%; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                <option value="every_5_minutes">Every 5 Minutes (Testing Only)</option>
                                <option value="every_15_minutes">Every 15 Minutes</option>
                                <option value="every_30_minutes">Every 30 Minutes</option>
                                <option value="hourly" selected>Every Hour</option>
                                <option value="twicedaily">Twice Daily (12 hours)</option>
                                <option value="daily">Once Daily (24 hours)</option>
                            </select>
                            <p style="color: #666; font-size: 13px; margin: 8px 0 0 0;">
                                All configured posts will be updated at this frequency
                            </p>
                        </div>
                        
                        <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); padding: 18px; border-radius: 10px; border-left: 4px solid #667eea;">
                            <div style="display: flex; align-items: start; gap: 10px;">
                                <span style="font-size: 24px;">💡</span>
                                <div>
                                    <strong style="color: #667eea; font-size: 14px;">How it works:</strong>
                                    <p style="margin: 8px 0 0 0; font-size: 13px; color: #555; line-height: 1.6;">
                                        Every time the schedule triggers, WordPress will automatically update <strong>all</strong> your configured posts. Choose a frequency that balances keeping content fresh with server load.
                                    </p>
                                    <p style="margin: 8px 0 0 0; font-size: 12px; color: #888;">
                                        💡 <em>Tip: Start with "Every Hour" and adjust based on your needs.</em>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button" onclick="document.getElementById('cron-modal').style.display='none'" style="margin-right: 10px;">Cancel</button>
                        <button type="button" id="save-cron-btn" class="button button-primary">
                            <span class="dashicons dashicons-yes"></span>
                            Save Settings
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Cron History Modal -->
            <div id="cron-history-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 900px;">
                    <div class="smartlink-modal-header">
                        <h2>
                            <span class="dashicons dashicons-backup"></span>
                            Scheduled Update History
                        </h2>
                        <button type="button" class="close-modal" onclick="document.getElementById('cron-history-modal').style.display='none'">×</button>
                    </div>
                    <div class="smartlink-modal-body">
                        <div id="cron-history-content" style="max-height: 500px; overflow-y: auto;">
                            <div style="text-align: center; padding: 40px;">
                                <span class="spinner is-active" style="float: none;"></span>
                                <p>Loading history...</p>
                            </div>
                        </div>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button" onclick="document.getElementById('cron-history-modal').style.display='none'">Close</button>
                        <button type="button" id="refresh-cron-history" class="button">
                            <span class="dashicons dashicons-image-rotate"></span>
                            Refresh
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Search and Filter Section -->
            <div class="smartlink-search-filter" style="background: white; padding: 20px 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border: 1px solid #e0e0e0;">
                <div style="display: flex; gap: 15px; align-items: flex-end; flex-wrap: wrap;">
                    <!-- Search Box -->
                    <div style="flex: 1; min-width: 250px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 13px;">
                            <span class="dashicons dashicons-search" style="font-size: 14px;"></span>
                            Search Posts
                        </label>
                        <input type="text" id="search-posts" placeholder="Search by title or ID..." style="width: 100%; padding: 10px 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; transition: border-color 0.2s;">
                    </div>
                    
                    <!-- Extractor Filter -->
                    <div style="min-width: 180px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 13px;">
                            <span class="dashicons dashicons-admin-tools" style="font-size: 14px;"></span>
                            Extractor
                        </label>
                        <select id="filter-extractor" style="width: 100%; padding: 10px 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; background: white;">
                            <option value="">All Extractors</option>
                            <option value="simplegameguide">Simple Game Guide</option>
                            <option value="techyhigher">Techy Higher</option>
                            <option value="mosttechs">Most Techs</option>
                            <option value="crazyashwin">Crazy Ashwin</option>
                        </select>
                    </div>
                    
                    <!-- Health Filter -->
                    <div style="min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 13px;">
                            <span class="dashicons dashicons-heart" style="font-size: 14px;"></span>
                            Health
                        </label>
                        <select id="filter-health" style="width: 100%; padding: 10px 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; background: white;">
                            <option value="">All Health</option>
                            <option value="healthy">Healthy</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                    </div>
                    
                    <!-- Status Filter -->
                    <div style="min-width: 150px;">
                        <label style="display: block; margin-bottom: 6px; font-weight: 600; color: #333; font-size: 13px;">
                            <span class="dashicons dashicons-info" style="font-size: 14px;"></span>
                            Status
                        </label>
                        <select id="filter-status" style="width: 100%; padding: 10px 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; background: white;">
                            <option value="">All Status</option>
                            <option value="idle">Idle</option>
                            <option value="updating">Updating</option>
                            <option value="completed">Completed</option>
                            <option value="failed">Failed</option>
                        </select>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div style="display: flex; gap: 8px;">
                        <button type="button" id="apply-filters" class="button button-primary" style="padding: 10px 20px; height: auto;">
                            <span class="dashicons dashicons-filter"></span>
                            Apply
                        </button>
                        <button type="button" id="clear-filters" class="button" style="padding: 10px 20px; height: auto;">
                            <span class="dashicons dashicons-dismiss"></span>
                            Clear
                        </button>
                    </div>
                </div>
                
                <!-- Active Filters Display -->
                <div id="active-filters" style="margin-top: 15px; display: none;">
                    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <span style="font-weight: 600; color: #666; font-size: 13px;">Active Filters:</span>
                        <div id="filter-tags" style="display: flex; gap: 8px; flex-wrap: wrap;"></div>
                    </div>
                </div>
            </div>
            
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
                            <th class="manage-column column-post-id">ID</th>
                            <th class="manage-column column-title">Post</th>
                            <th class="manage-column column-extractor">Extractor</th>
                            <th class="manage-column column-status">Status</th>
                            <th class="manage-column column-progress">Progress</th>
                            <th class="manage-column column-last-updated">Last Updated</th>
                            <th class="manage-column column-actions"></th>
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
            
            <!-- Post Config Modal (Add/Edit) -->
            <div id="post-config-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 800px;">
                    <div class="smartlink-modal-header">
                        <h2>
                            <span class="dashicons dashicons-admin-generic"></span>
                            <span id="config-modal-title">Add Post Configuration</span>
                        </h2>
                        <button type="button" class="close-modal" onclick="document.getElementById('post-config-modal').style.display='none'">×</button>
                    </div>
                    <div class="smartlink-modal-body">
                        <form id="post-config-form">
                            <input type="hidden" id="config-mode" value="add">
                            
                            <!-- Content Slug -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-tag" style="font-size: 16px; vertical-align: middle;"></span>
                                    Content Slug
                                </label>
                                <input type="text" id="config-content-slug" class="smartlink-input" placeholder="e.g., coin-master-free-spins"
                                       style="width: 100%; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                <p style="color: #666; font-size: 13px; margin: 8px 0 0 0;">
                                    Universal identifier for this content across all WordPress sites (optional but recommended for multi-site)
                                </p>
                            </div>
                            
                            <!-- Site-Specific Post IDs -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-admin-multisite" style="font-size: 16px; vertical-align: middle;"></span>
                                    Post IDs by Site
                                </label>
                                <div id="site-post-ids-container" style="background: #f9f9f9; padding: 15px; border-radius: 8px; border: 2px solid #ddd;">
                                    <p style="margin: 0 0 10px 0; font-size: 12px; color: #666;">Enter the post ID for each WordPress site. Leave blank if content doesn't exist on that site.</p>
                                    <div id="site-post-ids-fields"></div>
                                </div>
                            </div>
                            
                            <!-- Post ID (Legacy) -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-admin-post" style="font-size: 16px; vertical-align: middle;"></span>
                                    Legacy Post ID
                                </label>
                                <input type="number" id="config-post-id" class="smartlink-input" placeholder="e.g., 12345"
                                       style="width: 100%; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                <p style="color: #666; font-size: 13px; margin: 8px 0 0 0;">
                                    For backward compatibility. Use "Post IDs by Site" above for multi-site support.
                                </p>
                            </div>
                            
                            <!-- Source URLs -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-admin-links" style="font-size: 16px; vertical-align: middle;"></span>
                                    Source URLs *
                                </label>
                                <div id="source-urls-container">
                                    <div class="source-url-row" style="display: flex; gap: 8px; margin-bottom: 8px;">
                                        <input type="url" class="source-url-input smartlink-input" placeholder="https://example.com/links/" required
                                               style="flex: 1; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                        <button type="button" class="button remove-url-btn" style="display: none;">
                                            <span class="dashicons dashicons-no-alt"></span>
                                        </button>
                                    </div>
                                </div>
                                <button type="button" id="add-url-btn" class="button" style="margin-top: 8px;">
                                    <span class="dashicons dashicons-plus-alt"></span>
                                    Add Another URL
                                </button>
                                <p style="color: #666; font-size: 13px; margin: 8px 0 0 0;">
                                    URLs to scrape for daily links
                                </p>
                            </div>
                            
                            <!-- Extractor Configuration -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-admin-tools" style="font-size: 16px; vertical-align: middle;"></span>
                                    Extractor Configuration (Optional)
                                </label>
                                
                                <div style="margin-bottom: 12px;">
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                        <input type="radio" name="extractor-mode" value="auto" checked>
                                        <strong>Auto-detect for all URLs</strong> <span style="color: #666; font-size: 13px;">(Recommended - Smart detection based on URL)</span>
                                    </label>
                                </div>
                                
                                <div style="margin-bottom: 12px;">
                                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                                        <input type="radio" name="extractor-mode" value="per-url">
                                        <strong>Manually specify extractor per URL</strong>
                                    </label>
                                    <div id="per-url-extractor-config" style="display: none; margin-left: 28px; margin-top: 8px;">
                                        <p style="color: #666; font-size: 13px; margin-bottom: 12px;">
                                            <span class="dashicons dashicons-info" style="color: #2271b1;"></span>
                                            Only specify extractors for URLs where auto-detection doesn't work. Leave blank to auto-detect.
                                        </p>
                                        <div id="extractor-mapping-container"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Timezone -->
                            <div style="margin-bottom: 20px;">
                                <label style="display: block; margin-bottom: 8px; font-weight: 600; color: #333;">
                                    <span class="dashicons dashicons-clock" style="font-size: 16px; vertical-align: middle;"></span>
                                    Timezone
                                </label>
                                <select id="config-timezone" class="smartlink-select" style="width: 100%; padding: 12px; font-size: 14px; border: 2px solid #ddd; border-radius: 8px;">
                                    <option value="Asia/Kolkata" selected>Asia/Kolkata (IST)</option>
                                    <option value="America/New_York">America/New_York (EST)</option>
                                    <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                                    <option value="Europe/London">Europe/London (GMT)</option>
                                    <option value="UTC">UTC</option>
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button" onclick="document.getElementById('post-config-modal').style.display='none'">Cancel</button>
                        <button type="button" id="save-config-btn" class="button button-primary">
                            <span class="dashicons dashicons-yes"></span>
                            <span id="save-config-text">Save Configuration</span>
                        </button>
                    </div>
                </div>
            </div>
            
        </div>
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
        
        // List WordPress sites endpoint
        register_rest_route('smartlink/v1', '/sites', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_list_sites_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Post configuration endpoints
        register_rest_route('smartlink/v1', '/config/post', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_add_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/config/post/(?P<post_id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/config/post/(?P<post_id>\d+)', array(
            'methods' => 'PUT',
            'callback' => array($this, 'handle_update_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/config/post/(?P<post_id>\d+)', array(
            'methods' => 'DELETE',
            'callback' => array($this, 'handle_delete_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Cron settings endpoints
        register_rest_route('smartlink/v1', '/cron/settings', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_cron_settings_rest'),
            'permission_callback' => function() {
                return current_user_can('manage_options');
            }
        ));
        
        register_rest_route('smartlink/v1', '/cron/settings', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_save_cron_settings_rest'),
            'permission_callback' => function() {
                return current_user_can('manage_options');
            }
        ));
        
        register_rest_route('smartlink/v1', '/cron/status', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_cron_status_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/cron/history', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_cron_history_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Analytics endpoints
        register_rest_route('smartlink/v1', '/analytics/dashboard', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_dashboard_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/analytics/timeline', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_timeline_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/analytics/posts', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_posts_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/analytics/sources', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_sources_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/analytics/extractors', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_extractors_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        register_rest_route('smartlink/v1', '/analytics/sites', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_analytics_sites_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
    }

    /**
     * Handle analytics dashboard REST request
     */
    public function handle_get_analytics_dashboard_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $api_url = $this->api_base_url . '/api/analytics/dashboard?days=' . intval($days);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle analytics timeline REST request
     */
    public function handle_get_analytics_timeline_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $granularity = $request->get_param('granularity') ?: 'daily';
        $api_url = $this->api_base_url . '/api/analytics/timeline?days=' . intval($days) . '&granularity=' . urlencode($granularity);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle analytics posts REST request
     */
    public function handle_get_analytics_posts_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $api_url = $this->api_base_url . '/api/analytics/posts?days=' . intval($days);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle analytics sources REST request
     */
    public function handle_get_analytics_sources_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $api_url = $this->api_base_url . '/api/analytics/sources?days=' . intval($days);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle analytics extractors REST request
     */
    public function handle_get_analytics_extractors_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $api_url = $this->api_base_url . '/api/analytics/extractors?days=' . intval($days);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle analytics sites REST request
     */
    public function handle_get_analytics_sites_rest($request) {
        $days = $request->get_param('days') ?: 30;
        $api_url = $this->api_base_url . '/api/analytics/sites?days=' . intval($days);
        
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return rest_ensure_response($data);
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
        
        // Enrich posts with WordPress post titles
        if (isset($data['posts']) && is_array($data['posts'])) {
            foreach ($data['posts'] as &$post) {
                if (isset($post['post_id'])) {
                    $wp_post = get_post($post['post_id']);
                    if ($wp_post) {
                        $post['title'] = $wp_post->post_title;
                        $post['post_status'] = $wp_post->post_status;
                        $post['post_url'] = get_permalink($post['post_id']);
                    } else {
                        $post['title'] = 'Post ' . $post['post_id'] . ' (not found)';
                    }
                }
            }
        }
        
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
     * Handle list WordPress sites REST request (server-side proxy)
     */
    public function handle_list_sites_rest($request) {
        $api_url = $this->api_base_url . '/api/sites/list';
        
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
     * Handle add post config REST request (server-side proxy)
     */
    public function handle_add_post_config_rest($request) {
        $body = $request->get_json_params();
        
        if (empty($body)) {
            return new WP_Error('invalid_data', 'Request body is empty', array('status' => 400));
        }
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/config/post';
        
        $response = wp_remote_post($api_url, array(
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode($body),
            'timeout' => 15
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        if ($status_code >= 400) {
            return new WP_Error('api_error', $data['detail'] ?? 'Failed to add configuration', array('status' => $status_code));
        }
        
        return rest_ensure_response($data);
    }

    /**
     * Handle get post config REST request (server-side proxy)
     */
    public function handle_get_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
        $response = wp_remote_get($api_url, array(
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if ($status_code == 404) {
            return new WP_Error('not_found', 'Post configuration not found', array('status' => 404));
        }
        
        if ($status_code >= 400) {
            return new WP_Error('api_error', $data['detail'] ?? 'Failed to get configuration', array('status' => $status_code));
        }
        
        return rest_ensure_response($data);
    }

    /**
     * Handle update post config REST request (server-side proxy)
     */
    public function handle_update_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        $body = $request->get_json_params();
        
        if (empty($body)) {
            return new WP_Error('invalid_data', 'Request body is empty', array('status' => 400));
        }
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
        $response = wp_remote_request($api_url, array(
            'method' => 'PUT',
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode($body),
            'timeout' => 15
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        if ($status_code >= 400) {
            return new WP_Error('api_error', $data['detail'] ?? 'Failed to update configuration', array('status' => $status_code));
        }
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle delete post config REST request (server-side proxy)
     */
    public function handle_delete_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API (server-side)
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
        $response = wp_remote_request($api_url, array(
            'method' => 'DELETE',
            'timeout' => 15
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        if ($status_code == 404) {
            return new WP_Error('not_found', 'Post configuration not found', array('status' => 404));
        }
        
        if ($status_code >= 400) {
            return new WP_Error('api_error', $data['detail'] ?? 'Failed to delete configuration', array('status' => $status_code));
        }
        
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
    
    /**
     * Get cron settings REST endpoint
     */
    public function handle_get_cron_settings_rest($request) {
        $settings = get_option('smartlink_cron_settings', array(
            'enabled' => false,
            'schedule' => 'hourly'
        ));
        
        $last_run = get_option('smartlink_last_cron_batch');
        $next_run = wp_next_scheduled('slu_scheduled_update');
        
        return rest_ensure_response(array(
            'enabled' => $settings['enabled'],
            'schedule' => $settings['schedule'],
            'last_run' => $last_run,
            'next_run_timestamp' => $next_run
        ));
    }
    
    /**
     * Save cron settings REST endpoint
     */
    public function handle_save_cron_settings_rest($request) {
        $body = $request->get_json_params();
        
        if (empty($body)) {
            return new WP_Error('invalid_data', 'No data provided', array('status' => 400));
        }
        
        $settings = array(
            'enabled' => isset($body['enabled']) ? (bool)$body['enabled'] : false,
            'schedule' => isset($body['schedule']) ? sanitize_text_field($body['schedule']) : 'hourly'
        );
        
        update_option('smartlink_cron_settings', $settings);
        
        // Reschedule the cron based on new settings
        $timestamp = wp_next_scheduled('slu_scheduled_update');
        if ($timestamp) {
            wp_unschedule_event($timestamp, 'slu_scheduled_update');
        }
        
        if ($settings['enabled']) {
            wp_schedule_event(time(), $settings['schedule'], 'slu_scheduled_update');
        }
        
        return rest_ensure_response(array(
            'success' => true,
            'message' => 'Cron settings saved successfully'
        ));
    }
    
    /**
     * Get cron status REST endpoint
     */
    public function handle_get_cron_status_rest($request) {
        $settings = get_option('smartlink_cron_settings', array(
            'enabled' => false,
            'schedule' => 'hourly'
        ));
        
        $last_batch = get_option('smartlink_last_cron_batch');
        $next_run = wp_next_scheduled('slu_scheduled_update');
        
        // Get schedule label
        $schedules = wp_get_schedules();
        $schedule_label = isset($schedules[$settings['schedule']]) ? $schedules[$settings['schedule']]['display'] : 'Unknown';
        
        // Count total posts
        $api_url = $this->api_base_url . '/api/posts/list';
        $response = wp_remote_get($api_url, array('timeout' => 10));
        $total_posts = 0;
        
        if (!is_wp_error($response)) {
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);
            $total_posts = isset($data['posts']) ? count($data['posts']) : 0;
        }
        
        return rest_ensure_response(array(
            'enabled' => $settings['enabled'],
            'schedule' => $settings['schedule'],
            'schedule_label' => $schedule_label,
            'total_posts' => $total_posts,
            'last_run' => $last_batch ? date('Y-m-d H:i:s', $last_batch['timestamp']) : null,
            'next_run' => $next_run ? date('Y-m-d H:i:s', $next_run) : null
        ));
    }
    
    /**
     * Get cron history REST endpoint
     */
    public function handle_get_cron_history_rest($request) {
        $history = get_option('smartlink_cron_history', array());
        
        // Sort by timestamp descending (newest first)
        usort($history, function($a, $b) {
            return $b['timestamp'] - $a['timestamp'];
        });
        
        // Limit to last 50 entries
        $history = array_slice($history, 0, 50);
        
        // Format timestamps for display
        foreach ($history as &$entry) {
            $entry['formatted_time'] = date('Y-m-d H:i:s', $entry['timestamp']);
            $entry['time_ago'] = human_time_diff($entry['timestamp'], current_time('timestamp')) . ' ago';
        }
        
        return rest_ensure_response($history);
    }
    
    /**
     * Add custom cron schedules
     */
    public function add_cron_schedules($schedules) {
        $schedules['every_5_minutes'] = array(
            'interval' => 300,
            'display' => __('Every 5 Minutes (Testing)')
        );
        $schedules['every_15_minutes'] = array(
            'interval' => 900,
            'display' => __('Every 15 Minutes')
        );
        $schedules['every_30_minutes'] = array(
            'interval' => 1800,
            'display' => __('Every 30 Minutes')
        );
        return $schedules;
    }
    
    /**
     * Run scheduled update (WP-Cron job)
     */
    public function run_scheduled_update() {
        error_log('SmartLink: Scheduled update starting...');
        
        $settings = get_option('smartlink_cron_settings', array(
            'enabled' => false,
            'schedule' => 'hourly'
        ));
        
        if (!$settings['enabled']) {
            error_log('SmartLink: Cron is disabled, skipping');
            return;
        }
        
        // Get all configured posts from API
        $api_url = $this->api_base_url . '/api/posts/list';
        $response = wp_remote_get($api_url, array('timeout' => 10));
        
        if (is_wp_error($response)) {
            error_log('SmartLink: Failed to fetch posts - ' . $response->get_error_message());
            
            // Log error to history
            $this->add_cron_history_entry(array(
                'status' => 'error',
                'message' => 'Failed to fetch posts from API: ' . $response->get_error_message(),
                'post_count' => 0,
                'request_id' => null
            ));
            
            return;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (!isset($data['posts']) || empty($data['posts'])) {
            error_log('SmartLink: No posts found');
            
            // Log warning to history
            $this->add_cron_history_entry(array(
                'status' => 'warning',
                'message' => 'No configured posts found in database',
                'post_count' => 0,
                'request_id' => null
            ));
            
            return;
        }
        
        $posts = $data['posts'];
        $current_time = time();
        
        $posts_to_update = array();
        
        // Update ALL configured posts
        foreach ($posts as $post) {
            $posts_to_update[] = $post['post_id'];
        }
        
        if (empty($posts_to_update)) {
            error_log('SmartLink: No posts to update');
            return;
        }
        
        error_log('SmartLink: Triggering batch update for ALL ' . count($posts_to_update) . ' posts');
        
        // Trigger batch update via API
        $batch_api_url = $this->api_base_url . '/api/batch-update';
        $batch_response = wp_remote_post($batch_api_url, array(
            'timeout' => 30,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode(array(
                'post_ids' => $posts_to_update,
                'sync' => false,
                'target' => 'this',
                'initiator' => 'wp_cron'
            ))
        ));
        
        if (is_wp_error($batch_response)) {
            error_log('SmartLink: Batch update failed - ' . $batch_response->get_error_message());
            
            // Log failed attempt to history
            $this->add_cron_history_entry(array(
                'status' => 'error',
                'message' => 'Batch update API call failed: ' . $batch_response->get_error_message(),
                'post_count' => count($posts_to_update),
                'request_id' => null
            ));
            
            return;
        }
        
        $batch_body = wp_remote_retrieve_body($batch_response);
        $batch_data = json_decode($batch_body, true);
        
        if (isset($batch_data['request_id'])) {
            error_log('SmartLink: Batch update started - Request ID: ' . $batch_data['request_id']);
            
            // Save last batch info
            update_option('smartlink_last_cron_batch', array(
                'timestamp' => $current_time,
                'request_id' => $batch_data['request_id'],
                'post_count' => count($posts_to_update),
                'post_ids' => $posts_to_update
            ));
            
            // Log success to history
            $this->add_cron_history_entry(array(
                'status' => 'success',
                'message' => 'Batch update initiated successfully',
                'post_count' => count($posts_to_update),
                'request_id' => $batch_data['request_id'],
                'post_ids' => $posts_to_update
            ));
        } else {
            error_log('SmartLink: Batch update response missing request_id');
            
            // Log warning to history
            $this->add_cron_history_entry(array(
                'status' => 'warning',
                'message' => 'Batch update response missing request_id',
                'post_count' => count($posts_to_update),
                'request_id' => null
            ));
        }
    }
    
    /**
     * Add entry to cron history log
     */
    private function add_cron_history_entry($data) {
        $history = get_option('smartlink_cron_history', array());
        
        $entry = array(
            'timestamp' => time(),
            'status' => $data['status'],
            'message' => $data['message'],
            'post_count' => $data['post_count'],
            'request_id' => $data['request_id'],
            'post_ids' => isset($data['post_ids']) ? $data['post_ids'] : array()
        );
        
        // Add to beginning of array
        array_unshift($history, $entry);
        
        // Keep only last 100 entries
        $history = array_slice($history, 0, 100);
        
        update_option('smartlink_cron_history', $history);
    }
    
    /**
     * Render Analytics Page
     */
    public function render_analytics_page() {
        ?>
        <div class="wrap smartlink-analytics-wrap">
            <h1 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 30px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                <span class="dashicons dashicons-chart-bar" style="font-size: 32px;"></span>
                Analytics Dashboard
            </h1>
            
            <!-- Period Selector -->
            <div style="background: white; padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                <label for="analytics-period" style="margin-right: 10px; font-weight: 600;">Time Period:</label>
                <select id="analytics-period" class="smartlink-select">
                    <option value="7">Last 7 Days</option>
                    <option value="30" selected>Last 30 Days</option>
                    <option value="60">Last 60 Days</option>
                    <option value="90">Last 90 Days</option>
                </select>
                <button id="refresh-analytics" class="button button-primary" style="margin-left: 10px;">
                    <span class="dashicons dashicons-update"></span> Refresh
                </button>
            </div>
            
            <!-- Summary Cards -->
            <div id="summary-cards" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                <!-- Dynamically filled with JavaScript -->
            </div>
            
            <!-- Charts Row 1 -->
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin: 20px 0;">
                <div class="analytics-chart-container">
                    <h3>Update Timeline</h3>
                    <canvas id="timeline-chart"></canvas>
                </div>
                <div class="analytics-chart-container">
                    <h3>Success Rate</h3>
                    <canvas id="success-rate-chart"></canvas>
                </div>
            </div>
            
            <!-- Charts Row 2 -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <div class="analytics-chart-container">
                    <h3>Links Added Trend</h3>
                    <canvas id="links-trend-chart"></canvas>
                </div>
                <div class="analytics-chart-container">
                    <h3>Hourly Activity Pattern</h3>
                    <canvas id="hourly-pattern-chart"></canvas>
                </div>
            </div>
            
            <!-- Data Tables -->
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                <!-- Post Performance -->
                <div class="analytics-table-container">
                    <h3>Top Posts</h3>
                    <div id="post-performance-table"></div>
                </div>
                
                <!-- Source Performance -->
                <div class="analytics-table-container">
                    <h3>Source Performance</h3>
                    <div id="source-performance-table"></div>
                </div>
            </div>
            
            <!-- Extractor Performance -->
            <div class="analytics-table-container" style="margin: 20px 0;">
                <h3>Extractor Performance</h3>
                <div id="extractor-performance-table"></div>
            </div>
            
            <!-- Site Performance -->
            <div class="analytics-table-container" style="margin: 20px 0;">
                <h3>Multi-Site Performance</h3>
                <div id="site-performance-table"></div>
            </div>
        </div>
        <?php
    }
    
    /**
     * Print Analytics CSS
     */
    public function print_analytics_css() {
        ?>
        <style>
        .smartlink-analytics-wrap {
            max-width: 1400px;
        }
        
        .analytics-chart-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .analytics-chart-container h3 {
            margin-top: 0;
            color: #333;
            font-size: 18px;
            margin-bottom: 20px;
        }
        
        .analytics-chart-container canvas {
            max-height: 300px;
        }
        
        .analytics-table-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        
        .analytics-table-container h3 {
            margin-top: 0;
            color: #333;
            font-size: 18px;
            margin-bottom: 15px;
        }
        
        .analytics-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .analytics-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        
        .analytics-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .analytics-table tr:hover {
            background: #f8f9ff;
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border-left: 4px solid #667eea;
        }
        
        .summary-card h4 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .summary-card .value {
            font-size: 32px;
            font-weight: 700;
            color: #333;
            margin: 10px 0;
        }
        
        .summary-card .change {
            font-size: 14px;
            font-weight: 600;
        }
        
        .summary-card .change.positive {
            color: #10b981;
        }
        
        .summary-card .change.negative {
            color: #ef4444;
        }
        </style>
        <?php
    }
    
    /**
     * Print Analytics JavaScript
     */
    public function print_analytics_script() {
        ?>
        <script type="text/javascript">
        jQuery(document).ready(function($) {
            const config = window.SmartLinkConfig;
            let currentPeriod = 30;
            let charts = {};
            
            function loadAnalytics() {
                loadDashboardSummary();
                loadTimeline();
                loadLinksTrend();
                loadHourlyPattern();
                loadPostPerformance();
                loadSourcePerformance();
                loadExtractorPerformance();
                loadSitePerformance();
            }
            
            function loadDashboardSummary() {
                $.ajax({
                    url: config.restUrl + '/analytics/dashboard?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(data) {
                        renderSummaryCards(data);
                    }
                });
            }
            
            function renderSummaryCards(data) {
                const container = $('#summary-cards');
                container.html(`
                    <div class="summary-card">
                        <h4>Total Updates</h4>
                        <div class="value">${data.total_updates}</div>
                        <div class="change">${data.successful_updates} successful, ${data.failed_updates} failed</div>
                    </div>
                    <div class="summary-card">
                        <h4>Success Rate</h4>
                        <div class="value">${data.success_rate}%</div>
                    </div>
                    <div class="summary-card">
                        <h4>Links Added</h4>
                        <div class="value">${data.total_links_added}</div>
                        <div class="change">${data.avg_links_per_update.toFixed(2)} avg per update</div>
                    </div>
                    <div class="summary-card">
                        <h4>Active Posts</h4>
                        <div class="value">${data.active_posts}</div>
                    </div>
                `);
            }
            
            function loadTimeline() {
                $.ajax({
                    url: config.restUrl + '/analytics/timeline?days=' + currentPeriod + '&granularity=daily',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderTimelineChart(response.timeline);
                        renderSuccessRateChart(response.timeline);
                    }
                });
            }
            
            function renderTimelineChart(timeline) {
                const ctx = document.getElementById('timeline-chart');
                
                if (charts.timeline) {
                    charts.timeline.destroy();
                }
                
                charts.timeline = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: timeline.map(d => d.date),
                        datasets: [{
                            label: 'Successful',
                            data: timeline.map(d => d.successful),
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            tension: 0.4
                        }, {
                            label: 'Failed',
                            data: timeline.map(d => d.failed),
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function renderSuccessRateChart(timeline) {
                const ctx = document.getElementById('success-rate-chart');
                
                if (charts.successRate) {
                    charts.successRate.destroy();
                }
                
                const avgSuccessRate = timeline.reduce((sum, d) => sum + d.success_rate, 0) / timeline.length;
                const avgFailureRate = 100 - avgSuccessRate;
                
                charts.successRate = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Success', 'Failed'],
                        datasets: [{
                            data: [avgSuccessRate, avgFailureRate],
                            backgroundColor: ['#10b981', '#ef4444']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'bottom'
                            }
                        }
                    }
                });
            }
            
            function loadLinksTrend() {
                $.ajax({
                    url: config.restUrl + '/analytics/timeline?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderLinksTrendChart(response.timeline);
                    }
                });
            }
            
            function renderLinksTrendChart(timeline) {
                const ctx = document.getElementById('links-trend-chart');
                
                if (charts.linksTrend) {
                    charts.linksTrend.destroy();
                }
                
                charts.linksTrend = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: timeline.map(d => d.date),
                        datasets: [{
                            label: 'Links Added',
                            data: timeline.map(d => d.total_links),
                            backgroundColor: 'rgba(102, 126, 234, 0.7)',
                            borderColor: '#667eea',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function loadHourlyPattern() {
                $.ajax({
                    url: config.restUrl + '/analytics/hourly-pattern?days=7',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderHourlyPatternChart(response.hourly_pattern);
                    }
                });
            }
            
            function renderHourlyPatternChart(pattern) {
                const ctx = document.getElementById('hourly-pattern-chart');
                
                if (charts.hourlyPattern) {
                    charts.hourlyPattern.destroy();
                }
                
                charts.hourlyPattern = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: pattern.map(d => d.hour + ':00'),
                        datasets: [{
                            label: 'Updates',
                            data: pattern.map(d => d.total_updates),
                            backgroundColor: 'rgba(118, 75, 162, 0.7)',
                            borderColor: '#764ba2',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
            
            function loadPostPerformance() {
                $.ajax({
                    url: config.restUrl + '/analytics/posts?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderPostPerformanceTable(response.posts.slice(0, 10));
                    }
                });
            }
            
            function renderPostPerformanceTable(posts) {
                if (posts.length === 0) {
                    $('#post-performance-table').html('<p>No data available</p>');
                    return;
                }
                
                let html = '<table class="analytics-table">';
                html += '<thead><tr><th>Post ID</th><th>Updates</th><th>Success Rate</th><th>Links Added</th></tr></thead><tbody>';
                
                posts.forEach(post => {
                    html += `<tr>
                        <td>${post.post_id}${post.content_slug ? '<br><small>' + post.content_slug + '</small>' : ''}</td>
                        <td>${post.total_updates}</td>
                        <td>${post.success_rate}%</td>
                        <td>${post.total_links_added}</td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                $('#post-performance-table').html(html);
            }
            
            function loadSourcePerformance() {
                $.ajax({
                    url: config.restUrl + '/analytics/sources?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderSourcePerformanceTable(response.sources.slice(0, 10));
                    }
                });
            }
            
            function renderSourcePerformanceTable(sources) {
                if (sources.length === 0) {
                    $('#source-performance-table').html('<p>No data available</p>');
                    return;
                }
                
                let html = '<table class="analytics-table">';
                html += '<thead><tr><th>Source</th><th>Extractions</th><th>Success Rate</th><th>Health</th></tr></thead><tbody>';
                
                sources.forEach(source => {
                    const healthClass = source.current_health === 'healthy' ? 'health-good' : 
                                      source.current_health === 'warning' ? 'health-warning' : 'health-critical';
                    html += `<tr>
                        <td><small>${source.source_url}</small></td>
                        <td>${source.total_extractions}</td>
                        <td>${source.success_rate}%</td>
                        <td><span class="health-badge ${healthClass}">${source.current_health}</span></td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                $('#source-performance-table').html(html);
            }
            
            function loadExtractorPerformance() {
                $.ajax({
                    url: config.restUrl + '/analytics/extractors?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderExtractorPerformanceTable(response.extractors);
                    }
                });
            }
            
            function renderExtractorPerformanceTable(extractors) {
                if (extractors.length === 0) {
                    $('#extractor-performance-table').html('<p>No data available</p>');
                    return;
                }
                
                let html = '<table class="analytics-table">';
                html += '<thead><tr><th>Extractor</th><th>Updates</th><th>Success Rate</th><th>Links Extracted</th><th>Posts Using</th></tr></thead><tbody>';
                
                extractors.forEach(ext => {
                    html += `<tr>
                        <td>${ext.extractor}</td>
                        <td>${ext.total_updates}</td>
                        <td>${ext.success_rate}%</td>
                        <td>${ext.total_links_extracted}</td>
                        <td>${ext.posts_using}</td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                $('#extractor-performance-table').html(html);
            }
            
            function loadSitePerformance() {
                $.ajax({
                    url: config.restUrl + '/analytics/sites?days=' + currentPeriod,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        renderSitePerformanceTable(response.sites);
                    }
                });
            }
            
            function renderSitePerformanceTable(sites) {
                if (sites.length === 0) {
                    $('#site-performance-table').html('<p>No data available</p>');
                    return;
                }
                
                let html = '<table class="analytics-table">';
                html += '<thead><tr><th>Site</th><th>Links Added</th><th>Posts Updated</th><th>Avg Links/Post</th></tr></thead><tbody>';
                
                sites.forEach(site => {
                    html += `<tr>
                        <td>${site.site_key}</td>
                        <td>${site.total_links_added}</td>
                        <td>${site.unique_posts_updated}</td>
                        <td>${site.avg_links_per_post}</td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                $('#site-performance-table').html(html);
            }
            
            // Event handlers
            $('#analytics-period').on('change', function() {
                currentPeriod = parseInt($(this).val());
                loadAnalytics();
            });
            
            $('#refresh-analytics').on('click', function() {
                loadAnalytics();
            });
            
            // Initial load
            loadAnalytics();
        });
        </script>
        <?php
    }
}

// Initialize the plugin
$smartlink_updater = new SmartLinkUpdater();

// Register activation hook
register_activation_hook(__FILE__, 'smartlink_updater_activate');
function smartlink_updater_activate() {
    // Set default cron settings
    if (!get_option('smartlink_cron_settings')) {
        update_option('smartlink_cron_settings', array(
            'enabled' => false,
            'schedule' => 'hourly'
        ));
    }
    
    // Schedule the cron job (initially disabled until user enables it)
    if (!wp_next_scheduled('slu_scheduled_update')) {
        wp_schedule_event(time(), 'hourly', 'slu_scheduled_update');
    }
}

// Register deactivation hook
register_deactivation_hook(__FILE__, 'smartlink_updater_deactivate');
function smartlink_updater_deactivate() {
    // Clear the scheduled event
    $timestamp = wp_next_scheduled('slu_scheduled_update');
    if ($timestamp) {
        wp_unschedule_event($timestamp, 'slu_scheduled_update');
    }
}
