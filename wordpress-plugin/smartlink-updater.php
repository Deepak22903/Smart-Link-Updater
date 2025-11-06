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
            overflow-x: auto;
            overflow-y: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }

        .smartlink-posts-table {
            margin: 0;
            border-collapse: separate;
            border-spacing: 0;
            min-width: 1200px;
        }

        .smartlink-posts-table thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .smartlink-posts-table th {
            color: white;
            font-weight: 600;
            padding: 16px 12px;
            text-align: left;
            border: none;
            position: relative;
        }

        .sortable-header {
            cursor: pointer;
            user-select: none;
            transition: background 0.2s ease;
            padding-right: 30px !important;
        }

        .sortable-header:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .sort-indicator {
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 14px;
            opacity: 0.7;
            transition: all 0.2s ease;
        }

        .sortable-header:hover .sort-indicator {
            opacity: 1;
        }

        .sort-indicator.asc::before {
            content: '▲';
        }

        .sort-indicator.desc::before {
            content: '▼';
        }

        .sort-indicator:not(.asc):not(.desc)::before {
            content: '⇅';
            opacity: 0.5;
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
        
        .column-last-updated {
            width: 140px;
        }

        .column-status {
            width: 150px;
        }

        .column-progress {
            width: 120px;
        }

        .column-actions {
            width: 220px;
            min-width: 220px;
        }        .status-badge {
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
            cursor: help;
            position: relative;
            transition: all 0.3s ease;
        }

        .health-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
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

        /* Health Tooltip */
        .health-tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            margin-bottom: 8px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: normal;
            white-space: nowrap;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            min-width: 200px;
            text-align: left;
        }

        .health-tooltip::after {
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: rgba(0, 0, 0, 0.9);
        }

        .health-badge:hover .health-tooltip {
            opacity: 1;
            visibility: visible;
            transform: translateX(-50%) translateY(-4px);
        }

        .tooltip-line {
            display: block;
            margin-bottom: 4px;
        }

        .tooltip-line:last-child {
            margin-bottom: 0;
        }

        .tooltip-label {
            font-weight: 600;
            color: #ccc;
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
            position: relative;
            min-width: 220px;
            padding: 8px 12px !important;
        }
        
        .actions-wrapper {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .button-small {
            font-size: 12px;
            padding: 4px 8px;
            height: auto;
            line-height: 1.4;
            margin: 0;
            flex-shrink: 0;
        }
        
        /* Quick Actions Dropdown */
        .actions-menu {
            position: relative;
            display: inline-block;
            vertical-align: middle;
            flex-shrink: 0;
        }
        
        .actions-menu-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: 1px solid #5a67d8;
            border-radius: 4px;
            padding: 6px 8px;
            cursor: pointer;
            font-size: 12px;
            color: white;
            transition: all 0.2s;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 32px;
            height: 28px;
        }
        
        .actions-menu-btn:hover {
            background: linear-gradient(135deg, #5a67d8 0%, #6b3fa0 100%);
            border-color: #4c51bf;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(102, 126, 234, 0.4);
        }
        
        .actions-menu-btn .dashicons {
            font-size: 18px;
            width: 18px;
            height: 18px;
            line-height: 18px;
            color: white;
            margin: 0;
        }
        
        .actions-dropdown {
            display: none;
            position: absolute;
            right: 0;
            top: 100%;
            margin-top: 4px;
            background: white;
            border: 1px solid #c3c4c7;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            min-width: 180px;
        }
        
        .actions-dropdown.show {
            display: block;
            animation: dropdownSlide 0.15s ease-out;
        }
        
        @keyframes dropdownSlide {
            from {
                opacity: 0;
                transform: translateY(-8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .actions-dropdown-item {
            display: block;
            width: 100%;
            padding: 8px 12px;
            text-align: left;
            border: none;
            background: none;
            cursor: pointer;
            color: #2c3338;
            font-size: 13px;
            transition: background 0.15s;
            border-bottom: 1px solid #f0f0f1;
        }
        
        .actions-dropdown-item:last-child {
            border-bottom: none;
        }
        
        .actions-dropdown-item:hover {
            background: #f6f7f7;
        }
        
        .actions-dropdown-item.danger {
            color: #d63638;
        }
        
        .actions-dropdown-item.danger:hover {
            background: #fcf0f1;
        }
        
        .actions-dropdown-item .dashicons {
            font-size: 16px;
            width: 16px;
            height: 16px;
            line-height: 16px;
            vertical-align: middle;
            margin-right: 6px;
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

        /* Enhanced Log Content */
        .enhanced-log-content {
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 13px;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 0;
            border-radius: 8px;
            max-height: 500px;
            overflow-y: auto;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
            position: relative;
        }

        .log-loading {
            padding: 40px;
            text-align: center;
            color: #888;
        }

        .log-line {
            padding: 8px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            line-height: 1.6;
            position: relative;
            transition: background 0.2s ease;
        }

        .log-line:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .log-line:last-child {
            border-bottom: none;
        }

        .log-line.wrap-enabled {
            white-space: pre-wrap;
            word-break: break-word;
        }

        .log-line:not(.wrap-enabled) {
            white-space: nowrap;
            overflow-x: auto;
        }

        /* Log Level Styling */
        .log-line.level-DEBUG {
            border-left: 3px solid #6c757d;
            background: rgba(108, 117, 125, 0.1);
        }

        .log-line.level-INFO {
            border-left: 3px solid #17a2b8;
            background: rgba(23, 162, 184, 0.1);
        }

        .log-line.level-WARNING {
            border-left: 3px solid #ffc107;
            background: rgba(255, 193, 7, 0.1);
        }

        .log-line.level-ERROR {
            border-left: 3px solid #dc3545;
            background: rgba(220, 53, 69, 0.1);
        }

        /* Syntax Highlighting */
        .log-timestamp {
            color: #9cdcfe;
            font-weight: 600;
        }

        .log-level {
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }

        .log-level.DEBUG { background: #6c757d; color: white; }
        .log-level.INFO { background: #17a2b8; color: white; }
        .log-level.WARNING { background: #ffc107; color: #212529; }
        .log-level.ERROR { background: #dc3545; color: white; }

        .log-message {
            margin-left: 10px;
        }

        /* JSON Syntax Highlighting */
        .json-key {
            color: #9cdcfe;
        }

        .json-string {
            color: #ce9178;
        }

        .json-number {
            color: #b5cea8;
        }

        .json-boolean {
            color: #569cd6;
        }

        .json-null {
            color: #569cd6;
        }

        .json-punctuation {
            color: #d4d4d4;
        }

        /* Log Controls */
        .log-controls select,
        .log-controls input[type="checkbox"] {
            transition: all 0.2s ease;
        }

        .log-controls select:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
        }

        /* Scrollbar Styling */
        .enhanced-log-content::-webkit-scrollbar {
            width: 12px;
        }

        .enhanced-log-content::-webkit-scrollbar-track {
            background: #2d2d2d;
        }

        .enhanced-log-content::-webkit-scrollbar-thumb {
            background: #555;
            border-radius: 6px;
        }

        .enhanced-log-content::-webkit-scrollbar-thumb:hover {
            background: #777;
        }
        
        /* History Modal */
        .history-content {
            max-height: 450px;
            overflow-y: auto;
        }
        
        .history-timeline {
            position: relative;
            padding-left: 40px;
        }
        
        .history-item {
            position: relative;
            padding: 16px 20px;
            margin-bottom: 16px;
            background: white;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
            transition: all 0.2s;
        }
        
        .history-item:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            transform: translateX(4px);
        }
        
        .history-item.success {
            border-left-color: #10b981;
        }
        
        .history-item.failed {
            border-left-color: #ef4444;
        }
        
        .history-item::before {
            content: '';
            position: absolute;
            left: -44px;
            top: 20px;
            width: 12px;
            height: 12px;
            background: #667eea;
            border: 3px solid white;
            border-radius: 50%;
            box-shadow: 0 0 0 2px #667eea;
        }
        
        .history-item.success::before {
            background: #10b981;
            box-shadow: 0 0 0 2px #10b981;
        }
        
        .history-item.failed::before {
            background: #ef4444;
            box-shadow: 0 0 0 2px #ef4444;
        }
        
        .history-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .history-status {
            font-weight: 600;
            font-size: 14px;
        }
        
        .history-status.success {
            color: #10b981;
        }
        
        .history-status.failed {
            color: #ef4444;
        }
        
        .history-time {
            font-size: 12px;
            color: #666;
        }
        
        .history-details {
            font-size: 13px;
            color: #4b5563;
            line-height: 1.6;
        }
        
        .history-stats {
            display: flex;
            gap: 16px;
            margin-top: 8px;
            padding-top: 8px;
            border-top: 1px solid #f0f0f0;
            font-size: 12px;
        }
        
        .history-stat {
            color: #666;
        }
        
        .history-stat strong {
            color: #2c3338;
            font-weight: 600;
        }
        
        .history-empty {
            text-align: center;
            padding: 40px;
            color: #666;
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

        /* Search and Filter Styles */
        #search-posts:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .filter-group select:focus,
        .filter-group input:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .no-results-row {
            background: linear-gradient(135deg, #f8f9ff 0%, #fdf4ff 100%);
        }

        .no-results-row td {
            font-style: italic;
        }

        /* Batch Operations Dropdown */
        .batch-operations-dropdown {
            position: relative;
            display: inline-block;
        }

        #batch-operations-btn {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            border: none;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
        }

        #batch-operations-btn:hover:not(:disabled) {
            background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.4);
        }

        #batch-operations-btn:disabled {
            background: #ddd;
            color: #999;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .batch-dropdown-menu {
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 4px;
            background: white;
            border: 1px solid #c3c4c7;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            z-index: 1000;
            min-width: 220px;
            overflow: hidden;
            animation: dropdownSlide 0.2s ease-out;
        }

        .batch-operation-item {
            display: block;
            width: 100%;
            padding: 12px 16px;
            text-align: left;
            border: none;
            background: none;
            cursor: pointer;
            color: #2c3338;
            font-size: 14px;
            transition: all 0.15s ease;
            border-bottom: 1px solid #f0f0f1;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .batch-operation-item:last-child {
            border-bottom: none;
        }

        .batch-operation-item:hover {
            background: linear-gradient(135deg, #f8f9ff 0%, #fdf4ff 100%);
            color: #667eea;
        }

        .batch-operation-item[data-action="delete-selected"] {
            color: #d63638;
        }

        .batch-operation-item[data-action="delete-selected"]:hover {
            background: #fcf0f1;
            color: #d63638;
        }

        .batch-operation-item .dashicons {
            font-size: 16px;
            width: 16px;
            height: 16px;
            flex-shrink: 0;
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

            .smartlink-filters-container {
                flex-direction: column;
                align-items: stretch !important;
            }

            .filter-group {
                flex-direction: column;
                align-items: stretch !important;
            }

            .filter-group label {
                margin-bottom: 5px;
            }

            #search-posts {
                min-width: auto !important;
                width: 100%;
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
                
                // Enhanced log controls
                $('#log-level-filter').on('change', filterLogsByLevel);
                $('#clear-log-display').on('click', clearLogDisplay);
                $('#wrap-lines-logs').on('change', toggleLineWrap);
                $('#export-logs').on('click', exportLogs);
                
                // Batch operations dropdown
                $('#batch-operations-btn').on('click', toggleBatchOperationsMenu);
                $(document).on('click', '.batch-operation-item', handleBatchOperation);
                
                // Edit Config Modal
                $('.close-edit-modal').on('click', closeEditModal);
                $('#save-config-btn').on('click', saveConfigChanges);
                
                // History Modal
                $('.close-history-modal').on('click', closeHistoryModal);
                $('#refresh-history').on('click', refreshHistory);
                
                // Delegate checkbox change event
                $(document).on('change', '.post-checkbox', updateSelectedCount);
                $(document).on('click', '.view-logs-btn', viewLogs);
                $(document).on('click', '.single-update-btn', singleUpdate);
                
                // Quick Actions Menu
                $(document).on('click', '.actions-menu-btn', toggleActionsMenu);
                $(document).on('click', '.edit-config-btn', editConfig);
                $(document).on('click', '.view-history-btn', viewHistory);
                $(document).on('click', '.reset-health-btn', resetHealth);
                $(document).on('click', '.delete-config-btn', deleteConfig);
                
                // Filter and search event listeners
                $('#search-posts').on('input', debounce(applyFilters, 300));
                $('#filter-health').on('change', applyFilters);
                $('#filter-extractor').on('change', applyFilters);
                $('#clear-filters').on('click', clearFilters);
                
                // Sortable headers
                $(document).on('click', '.sortable-header', handleSort);
                
                // Close dropdown when clicking outside
                $(document).on('click', function(e) {
                    if (!$(e.target).closest('.actions-menu').length) {
                        $('.actions-dropdown').removeClass('show');
                    }
                    if (!$(e.target).closest('.batch-operations-dropdown').length) {
                        $('#batch-operations-menu').hide();
                    }
                });
            }
            
            // ========== LOAD POSTS ==========
            
            function showLoadingState() {
                $('#posts-table-body').html(`
                    <tr>
                        <td colspan="9" style="text-align: center; padding: 40px;">
                            <div style="display: flex; align-items: center; justify-content: center; gap: 10px;">
                                <span class="spinner is-active" style="float: none; margin: 0;"></span>
                                <span style="color: #666; font-size: 16px;">Loading posts...</span>
                            </div>
                        </td>
                    </tr>
                `);
                
                // Also disable refresh button during loading
                $('#refresh-posts').prop('disabled', true);
            }
            
            function formatRelativeTime(timestamp) {
                if (!timestamp) return 'Never';
                
                const now = new Date();
                const date = new Date(timestamp);
                const seconds = Math.floor((now - date) / 1000);
                
                if (seconds < 60) return 'Just now';
                if (seconds < 3600) return Math.floor(seconds / 60) + ' mins ago';
                if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
                if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
                if (seconds < 2592000) return Math.floor(seconds / 604800) + ' weeks ago';
                if (seconds < 31536000) return Math.floor(seconds / 2592000) + ' months ago';
                return Math.floor(seconds / 31536000) + ' years ago';
            }
            
            function loadPosts() {
                // Show loading state
                showLoadingState();
                
                $.ajax({
                    url: config.restUrl + '/posts',
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        postsData = response.posts || [];
                        renderPostsTable(postsData);
                        showToast('Posts loaded successfully', 'success');
                        $('#refresh-posts').prop('disabled', false);
                    },
                    error: function(xhr) {
                        console.error('Failed to load posts:', xhr);
                        const errorMsg = xhr.responseJSON && xhr.responseJSON.message 
                            ? xhr.responseJSON.message 
                            : 'Failed to load posts. Please check your connection.';
                        showToast(errorMsg, 'error');
                        
                        // Show empty state with retry option
                        $('#posts-table-body').html(`
                            <tr>
                                <td colspan="9" style="text-align: center; padding: 40px;">
                                    <div style="color: #dc3232; margin-bottom: 15px;">
                                        <span class="dashicons dashicons-warning" style="font-size: 24px;"></span><br>
                                        Failed to load posts
                                    </div>
                                    <p style="margin-bottom: 20px; color: #666;">${errorMsg}</p>
                                    <button type="button" id="retry-load-posts" class="button button-primary">
                                        <span class="dashicons dashicons-update"></span> Retry
                                    </button>
                                </td>
                            </tr>
                        `);
                        
                        // Add retry functionality
                        $(document).on('click', '#retry-load-posts', function() {
                            loadPosts();
                        });
                        
                        $('#refresh-posts').prop('disabled', false);
                    }
                });
            }
            
            function renderPostsTable(posts) {
                const tbody = $('#posts-table-body');
                tbody.empty();
                
                if (posts.length === 0) {
                    tbody.append('<tr><td colspan="9" style="text-align: center; padding: 40px;">No configured posts found.</td></tr>');
                    return;
                }
                
                // Update statistics
                updateStatistics(posts);
                
                // Initialize filtered data and populate extractor filter
                filteredPostsData = [...posts];
                populateExtractorFilter();
                
                posts.forEach(function(post) {
                    renderSinglePost(post, tbody);
                });
            }
            
            function renderSinglePost(post, tbody) {
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
                    
                    // Title (fetch from WordPress)
                    const titleCell = $('<td>').html('<span class="spinner is-active" style="float: none; margin: 0;"></span>');
                    row.append(titleCell);
                    
                    // Fetch post title from WordPress
                    fetchPostTitle(post.post_id, titleCell);
                    
                    // Extractor
                    row.append($('<td>').text(post.extractor || 'default'));
                    
                    // Health Status
                    const healthBadge = getHealthBadge(post.health_status);
                    row.append($('<td>').html(healthBadge));
                    
                    // Last Updated
                    const lastUpdated = formatRelativeTime(post.updated_at);
                    row.append($('<td>').html(
                        '<span style="color: #666; font-size: 12px;">' + lastUpdated + '</span>'
                    ));
                    
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
                    
                    // Create actions wrapper - horizontal layout
                    const actionsWrapper = $('<div>').addClass('actions-wrapper');
                    
                    // Quick Actions Menu - FIRST (on the left)
                    const actionsMenu = $('<div>').addClass('actions-menu');
                    const menuBtn = $('<button>').addClass('actions-menu-btn').attr('data-post-id', post.post_id).html(
                        '<span class="dashicons dashicons-menu"></span>'
                    ).attr('title', 'More Actions');
                    const dropdown = $('<div>').addClass('actions-dropdown').html(`
                        <button class="actions-dropdown-item edit-config-btn" data-post-id="${post.post_id}">
                            <span class="dashicons dashicons-edit"></span> Edit Config
                        </button>
                        <button class="actions-dropdown-item view-history-btn" data-post-id="${post.post_id}">
                            <span class="dashicons dashicons-backup"></span> View History
                        </button>
                        <button class="actions-dropdown-item reset-health-btn" data-post-id="${post.post_id}">
                            <span class="dashicons dashicons-heart"></span> Reset Health
                        </button>
                        <button class="actions-dropdown-item danger delete-config-btn" data-post-id="${post.post_id}">
                            <span class="dashicons dashicons-trash"></span> Delete Config
                        </button>
                    `);
                    actionsMenu.append(menuBtn).append(dropdown);
                    
                    // Primary action buttons - AFTER menu
                    const updateBtn = $('<button>').addClass('button button-small single-update-btn').attr('data-post-id', post.post_id).html(
                        '<span class="dashicons dashicons-update"></span> Update'
                    );
                    
                    const logsBtn = $('<button>').addClass('button button-small view-logs-btn').attr({
                        'data-post-id': post.post_id,
                        'disabled': true
                    }).html(
                        '<span class="dashicons dashicons-media-text"></span> Logs'
                    );
                    
                    // Assemble: Menu first, then buttons
                    actionsWrapper.append(actionsMenu).append(updateBtn).append(logsBtn);
                    actionsCell.append(actionsWrapper);
                    
                    row.append(actionsCell);
                    
                    tbody.append(row);
            }
            
            function getHealthBadge(healthData) {
                // Handle both old string format and new object format
                if (typeof healthData === 'string') {
                    healthData = { status: healthData };
                }
                
                const status = healthData.status || 'unknown';
                const lastCheck = healthData.last_check || null;
                const errorCount = healthData.error_count || 0;
                const issues = healthData.issues || [];
                
                // Create tooltip content
                let tooltipContent = '';
                if (lastCheck) {
                    tooltipContent += `<span class="tooltip-line"><span class="tooltip-label">Last Check:</span> ${formatRelativeTime(lastCheck)}</span>`;
                }
                tooltipContent += `<span class="tooltip-line"><span class="tooltip-label">Status:</span> ${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;
                if (errorCount > 0) {
                    tooltipContent += `<span class="tooltip-line"><span class="tooltip-label">Errors:</span> ${errorCount}</span>`;
                }
                if (issues.length > 0) {
                    tooltipContent += `<span class="tooltip-line"><span class="tooltip-label">Issues:</span> ${issues.join(', ')}</span>`;
                }
                
                const badges = {
                    'healthy': `<span class="health-badge health-good">✓ Healthy<div class="health-tooltip">${tooltipContent}</div></span>`,
                    'warning': `<span class="health-badge health-warning">⚠ Warning<div class="health-tooltip">${tooltipContent}</div></span>`,
                    'critical': `<span class="health-badge health-critical">✗ Critical<div class="health-tooltip">${tooltipContent}</div></span>`,
                    'unknown': `<span class="health-badge health-unknown">? Unknown<div class="health-tooltip">${tooltipContent}</div></span>`
                };
                return badges[status] || badges['unknown'];
            }
            
            function fetchPostTitle(postId, titleLink) {
                $.ajax({
                    url: '/wp-json/wp/v2/posts/' + postId,
                    method: 'GET',
                    success: function(response) {
                        const title = response.title.rendered || 'Post ' + postId;
                        const editLink = '/wp-admin/post.php?post=' + postId + '&action=edit';
                        titleLink.attr('href', editLink).attr('target', '_blank').html(escapeHtml(title));
                    },
                    error: function() {
                        titleLink.text('Post ' + postId + ' (Title not found)');
                    }
                });
            }
            
            function updateStatistics(posts) {
                const totalPosts = posts.length;
                $('#stat-total-posts').text(totalPosts);
                
                // These will be updated dynamically during batch updates
                // For now, show initial state
                $('#stat-active-updates').text('0');
                $('#stat-success-rate').text('-');
                $('#stat-failed-updates').text('0');
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
                $('#batch-operations-btn').prop('disabled', count === 0);
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
                let successCount = 0;
                let failedCount = 0;
                let activeCount = 0;
                
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
                    
                    // Count statistics
                    if (postState.status === 'success' || postState.status === 'no_changes') {
                        completedCount++;
                        successCount++;
                    } else if (postState.status === 'failed') {
                        completedCount++;
                        failedCount++;
                    } else if (postState.status === 'running') {
                        activeCount++;
                    }
                });
                
                // Update overall progress
                const overallProgress = Math.round((completedCount / totalPosts) * 100);
                $('#completed-posts').text(completedCount);
                $('#overall-progress-fill').css('width', overallProgress + '%');
                
                // Update statistics cards
                $('#stat-active-updates').text(activeCount);
                $('#stat-failed-updates').text(failedCount);
                if (completedCount > 0) {
                    const successRate = Math.round((successCount / completedCount) * 100);
                    $('#stat-success-rate').text(successRate + '%');
                }
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
            
            // ========== QUICK ACTIONS MENU ==========
            
            function toggleActionsMenu(e) {
                e.stopPropagation();
                const dropdown = $(e.currentTarget).siblings('.actions-dropdown');
                
                // Close all other dropdowns
                $('.actions-dropdown').not(dropdown).removeClass('show');
                
                // Toggle this dropdown
                dropdown.toggleClass('show');
            }
            
            function editConfig(e) {
                e.stopPropagation();
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                // Close dropdown
                $('.actions-dropdown').removeClass('show');
                
                // Load current config
                $.ajax({
                    url: config.restUrl + '/post/' + postId,
                    method: 'GET',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        const postConfig = response.config;
                        
                        // Populate form
                        $('#edit-post-id').text(postId);
                        $('#edit-extractor').val(postConfig.extractor || '');
                        $('#edit-source-url').val(postConfig.source_urls?.[0] || '');
                        $('#edit-timezone').val(postConfig.timezone || 'Asia/Kolkata');
                        
                        // Store post ID in form
                        $('#edit-config-form').data('post-id', postId);
                        
                        // Show modal
                        $('#edit-config-modal').fadeIn();
                    },
                    error: function(xhr) {
                        showToast('Failed to load config: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            function closeEditModal() {
                $('#edit-config-modal').fadeOut();
            }
            
            function saveConfigChanges() {
                const postId = $('#edit-config-form').data('post-id');
                const extractor = $('#edit-extractor').val();
                const sourceUrl = $('#edit-source-url').val();
                const timezone = $('#edit-timezone').val();
                
                // Validate
                if (!sourceUrl) {
                    showToast('Source URL is required', 'error');
                    return;
                }
                
                // Prepare update data
                const updateData = {
                    source_urls: [sourceUrl],
                    timezone: timezone || 'Asia/Kolkata'
                };
                
                if (extractor) {
                    updateData.extractor = extractor;
                }
                
                // Disable button
                const $btn = $('#save-config-btn');
                $btn.prop('disabled', true).html('<span class="spinner is-active" style="float: none;"></span> Saving...');
                
                $.ajax({
                    url: config.restUrl + '/post/' + postId,
                    method: 'PUT',
                    contentType: 'application/json',
                    data: JSON.stringify(updateData),
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        showToast('Configuration updated for post ' + postId, 'success');
                        closeEditModal();
                        loadPosts(); // Reload to show updated config
                    },
                    error: function(xhr) {
                        showToast('Failed to update config: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    },
                    complete: function() {
                        $btn.prop('disabled', false).html('<span class="dashicons dashicons-saved"></span> Save Changes');
                    }
                });
            }
            
            function viewHistory(e) {
                e.stopPropagation();
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                // Close dropdown
                $('.actions-dropdown').removeClass('show');
                
                // Show modal
                $('#history-post-id').text(postId);
                $('#history-content').html('<span class="spinner is-active"></span> Loading update history...');
                $('#history-modal').fadeIn();
                
                // Load history
                loadHistory(postId);
            }
            
            function loadHistory(postId) {
                // For now, we'll show a message that this feature requires backend support
                // In the future, we can create an endpoint to track update history
                
                const historyHtml = `
                    <div class="history-timeline">
                        <div class="history-item success">
                            <div class="history-header">
                                <div class="history-status success">✓ Update Completed</div>
                                <div class="history-time">2 hours ago</div>
                            </div>
                            <div class="history-details">
                                Links successfully updated from source URL
                            </div>
                            <div class="history-stats">
                                <div class="history-stat"><strong>12</strong> links found</div>
                                <div class="history-stat"><strong>8</strong> links updated</div>
                                <div class="history-stat"><strong>2</strong> links added</div>
                            </div>
                        </div>
                        
                        <div class="history-item success">
                            <div class="history-header">
                                <div class="history-status success">✓ Update Completed</div>
                                <div class="history-time">1 day ago</div>
                            </div>
                            <div class="history-details">
                                Links successfully updated from source URL
                            </div>
                            <div class="history-stats">
                                <div class="history-stat"><strong>10</strong> links found</div>
                                <div class="history-stat"><strong>7</strong> links updated</div>
                                <div class="history-stat"><strong>1</strong> link added</div>
                            </div>
                        </div>
                        
                        <div class="history-item failed">
                            <div class="history-header">
                                <div class="history-status failed">✗ Update Failed</div>
                                <div class="history-time">3 days ago</div>
                            </div>
                            <div class="history-details">
                                Failed to extract links: Source page structure changed
                            </div>
                        </div>
                        
                        <div style="padding: 20px; text-align: center; background: #f0f8ff; border-radius: 8px; margin-top: 20px;">
                            <p style="margin: 0; color: #666;">
                                <span class="dashicons dashicons-info" style="color: #2271b1;"></span>
                                <strong>Note:</strong> Full update history tracking is coming soon!<br>
                                <small>This is a preview of what the history feature will look like.</small>
                            </p>
                        </div>
                    </div>
                `;
                
                $('#history-content').html(historyHtml);
            }
            
            function closeHistoryModal() {
                $('#history-modal').fadeOut();
            }
            
            function refreshHistory() {
                const postId = parseInt($('#history-post-id').text());
                if (postId) {
                    loadHistory(postId);
                }
            }
            
            function resetHealth(e) {
                e.stopPropagation();
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                // Close dropdown
                $('.actions-dropdown').removeClass('show');
                
                if (!confirm('Reset health status for post ' + postId + ' to Unknown?')) {
                    return;
                }
                
                $.ajax({
                    url: config.restUrl + '/post/' + postId,
                    method: 'PUT',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        health_status: 'unknown'
                    }),
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        showToast('Health status reset for post ' + postId, 'success');
                        loadPosts(); // Reload to show updated health
                    },
                    error: function(xhr) {
                        showToast('Failed to reset health: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            function deleteConfig(e) {
                e.stopPropagation();
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                // Close dropdown
                $('.actions-dropdown').removeClass('show');
                
                if (!confirm('Are you sure you want to delete the configuration for post ' + postId + '?\n\nThis action cannot be undone.')) {
                    return;
                }
                
                $.ajax({
                    url: config.restUrl + '/posts/' + postId,
                    method: 'DELETE',
                    beforeSend: function(xhr) {
                        xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                    },
                    success: function(response) {
                        showToast('Configuration deleted for post ' + postId, 'success');
                        loadPosts(); // Reload to remove deleted post
                    },
                    error: function(xhr) {
                        showToast('Failed to delete config: ' + (xhr.responseJSON?.message || 'Unknown error'), 'error');
                    }
                });
            }
            
            // ========== LOGS MODAL ==========
            
            let currentLogData = [];
            let filteredLogData = [];
            
            function viewLogs(e) {
                const postId = parseInt($(e.currentTarget).data('post-id'));
                
                if (!currentBatchRequestId) {
                    showToast('No active batch request. Start a batch update first.', 'warning');
                    return;
                }
                
                $('#log-post-id').text(postId);
                $('#log-content').html('<div class="log-loading"><span class="spinner is-active"></span>Loading logs...</div>');
                $('#logs-modal').fadeIn();
                
                // Reset controls
                $('#log-level-filter').val('');
                $('#auto-scroll-logs').prop('checked', true);
                $('#wrap-lines-logs').prop('checked', false);
                
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
                            $('#log-content').html('<div style="text-align: center; color: #888; padding: 40px;">No logs available for this post</div>');
                            return;
                        }
                        
                        // Process and store log data
                        currentLogData = logs.map(function(log, index) {
                            return parseLogEntry(log, index);
                        });
                        
                        filteredLogData = [...currentLogData];
                        renderLogs();
                        
                        // Auto-scroll to bottom if enabled
                        if ($('#auto-scroll-logs').prop('checked')) {
                            autoScrollToBottom();
                        }
                    },
                    error: function() {
                        $('#log-content').html('<p style="text-align: center; color: #dc3232;">Failed to load logs</p>');
                    }
                });
            }
            
            function refreshLogs() {
                const postId = parseInt($('#log-post-id').text());
                if (postId) {
                    $('#log-content').html('<div class="log-loading"><span class="spinner is-active"></span>Refreshing logs...</div>');
                    loadLogs(postId);
                }
            }
            
            function parseLogEntry(logString, index) {
                // Try to parse structured log entry
                const timestampRegex = /^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})/;
                const levelRegex = /(DEBUG|INFO|WARNING|ERROR|WARN)/i;
                
                const timestampMatch = logString.match(timestampRegex);
                const levelMatch = logString.match(levelRegex);
                
                let timestamp = timestampMatch ? timestampMatch[1] : null;
                let level = levelMatch ? levelMatch[1].toUpperCase() : 'INFO';
                let message = logString;
                
                // Remove timestamp and level from message
                if (timestampMatch) {
                    message = message.substring(timestampMatch[0].length).trim();
                }
                if (levelMatch) {
                    message = message.replace(levelMatch[0], '').trim();
                    message = message.replace(/^[:\-\s]*/, ''); // Remove separators
                }
                
                return {
                    id: index,
                    timestamp: timestamp,
                    level: level,
                    message: message,
                    original: logString
                };
            }
            
            function renderLogs() {
                const container = $('#log-content');
                const wrapLines = $('#wrap-lines-logs').prop('checked');
                
                if (filteredLogData.length === 0) {
                    container.html('<div style="text-align: center; color: #888; padding: 40px;">No logs match the current filter</div>');
                    return;
                }
                
                const logHtml = filteredLogData.map(function(logEntry) {
                    const wrapClass = wrapLines ? 'wrap-enabled' : '';
                    const levelClass = 'level-' + logEntry.level;
                    
                    let content = '';
                    if (logEntry.timestamp) {
                        content += `<span class="log-timestamp">[${logEntry.timestamp}]</span> `;
                    }
                    content += `<span class="log-level ${logEntry.level}">${logEntry.level}</span>`;
                    content += `<span class="log-message">${formatLogMessage(logEntry.message)}</span>`;
                    
                    return `<div class="log-line ${levelClass} ${wrapClass}">${content}</div>`;
                }).join('');
                
                container.html(logHtml);
            }
            
            function formatLogMessage(message) {
                // Basic JSON syntax highlighting
                if (message.trim().startsWith('{') && message.trim().endsWith('}')) {
                    try {
                        const parsed = JSON.parse(message);
                        return syntaxHighlightJSON(parsed);
                    } catch (e) {
                        // Fall back to regular escaping
                    }
                }
                
                return escapeHtml(message);
            }
            
            function syntaxHighlightJSON(obj) {
                const json = JSON.stringify(obj, null, 2);
                return json
                    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                        let cls = 'json-number';
                        if (/^"/.test(match)) {
                            if (/:$/.test(match)) {
                                cls = 'json-key';
                            } else {
                                cls = 'json-string';
                            }
                        } else if (/true|false/.test(match)) {
                            cls = 'json-boolean';
                        } else if (/null/.test(match)) {
                            cls = 'json-null';
                        }
                        return '<span class="' + cls + '">' + match + '</span>';
                    })
                    .replace(/([{}[\],:])/g, '<span class="json-punctuation">$1</span>');
            }
            
            function filterLogsByLevel() {
                const selectedLevel = $('#log-level-filter').val();
                
                if (!selectedLevel) {
                    filteredLogData = [...currentLogData];
                } else {
                    filteredLogData = currentLogData.filter(log => log.level === selectedLevel);
                }
                
                renderLogs();
                
                // Auto-scroll to bottom if enabled
                if ($('#auto-scroll-logs').prop('checked')) {
                    setTimeout(autoScrollToBottom, 100);
                }
            }
            
            function clearLogDisplay() {
                $('#log-content').html('<div style="text-align: center; color: #888; padding: 40px;">Log display cleared</div>');
            }
            
            function toggleLineWrap() {
                renderLogs();
            }
            
            function autoScrollToBottom() {
                const logContainer = document.getElementById('log-content');
                if (logContainer) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }
            }
            
            function exportLogs() {
                if (!currentLogData || currentLogData.length === 0) {
                    showToast('No logs to export', 'warning');
                    return;
                }
                
                const postId = $('#log-post-id').text();
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const filename = `smartlink-logs-post-${postId}-${timestamp}.txt`;
                
                // Use filtered data if filter is active
                const dataToExport = filteredLogData.length > 0 ? filteredLogData : currentLogData;
                
                const logText = dataToExport.map(log => log.original).join('\n');
                
                // Create and download file
                const blob = new Blob([logText], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                showToast('Logs exported successfully', 'success');
            }
            
            function closeLogsModal() {
                $('#logs-modal').fadeOut();
                currentLogData = [];
                filteredLogData = [];
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
            
            // ========== SORTING ==========
            
            let currentSort = { column: null, direction: null };
            
            function handleSort(e) {
                const header = $(e.currentTarget);
                const column = header.data('sort');
                const currentDirection = header.find('.sort-indicator').hasClass('asc') ? 'asc' 
                    : header.find('.sort-indicator').hasClass('desc') ? 'desc' : null;
                
                let newDirection;
                if (currentDirection === null) {
                    newDirection = 'asc';
                } else if (currentDirection === 'asc') {
                    newDirection = 'desc';
                } else {
                    newDirection = null;
                }
                
                // Clear all sort indicators
                $('.sort-indicator').removeClass('asc desc');
                
                // Set new sort indicator
                if (newDirection) {
                    header.find('.sort-indicator').addClass(newDirection);
                    currentSort = { column: column, direction: newDirection };
                } else {
                    currentSort = { column: null, direction: null };
                }
                
                // Apply sort
                applySorting();
            }
            
            function applySorting() {
                if (!currentSort.column) {
                    // No sorting, use original order
                    renderPostsTable(postsData);
                    return;
                }
                
                const sortedData = [...filteredPostsData].sort((a, b) => {
                    let aVal = getSortValue(a, currentSort.column);
                    let bVal = getSortValue(b, currentSort.column);
                    
                    // Handle null/undefined values
                    if (aVal == null && bVal == null) return 0;
                    if (aVal == null) return currentSort.direction === 'asc' ? 1 : -1;
                    if (bVal == null) return currentSort.direction === 'asc' ? -1 : 1;
                    
                    // Compare values
                    if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
                    if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
                    return 0;
                });
                
                renderSortedTable(sortedData);
            }
            
            function getSortValue(post, column) {
                switch (column) {
                    case 'post_id':
                        return parseInt(post.post_id);
                    case 'title':
                        // Get title from the table cell since we fetch it asynchronously
                        const titleCell = $('#posts-table-body tr[data-post-id="' + post.post_id + '"] td:nth-child(3)');
                        return titleCell.text().toLowerCase();
                    case 'extractor':
                        return (post.extractor || 'default').toLowerCase();
                    case 'health_status':
                        const healthOrder = { 'healthy': 0, 'warning': 1, 'critical': 2, 'unknown': 3 };
                        return healthOrder[post.health_status] ?? 3;
                    case 'updated_at':
                        return post.updated_at ? new Date(post.updated_at).getTime() : 0;
                    default:
                        return '';
                }
            }
            
            function renderSortedTable(sortedPosts) {
                const tbody = $('#posts-table-body');
                
                // Clear tbody
                tbody.empty();
                
                if (sortedPosts.length === 0) {
                    tbody.append('<tr class="no-results-row"><td colspan="9" style="text-align: center; padding: 40px; color: #666;">No posts match the current filters.</td></tr>');
                    return;
                }
                
                // Re-render posts in sorted order
                sortedPosts.forEach(function(post) {
                    // Find existing row and move it, or create new row
                    let existingRow = tbody.find('tr[data-post-id="' + post.post_id + '"]');
                    if (existingRow.length === 0) {
                        // Create new row (shouldn't happen but safety)
                        renderSinglePost(post, tbody);
                    } else {
                        // Move existing row to maintain sorting
                        tbody.append(existingRow);
                    }
                });
                
                updateSelectedCount();
            }
            
            // ========== BATCH OPERATIONS ==========
            
            function toggleBatchOperationsMenu(e) {
                e.stopPropagation();
                const menu = $('#batch-operations-menu');
                menu.toggle();
            }
            
            function handleBatchOperation(e) {
                const action = $(e.currentTarget).data('action');
                const selectedIds = getSelectedPostIds();
                
                if (selectedIds.length === 0) {
                    showToast('No posts selected', 'warning');
                    return;
                }
                
                // Close dropdown
                $('#batch-operations-menu').hide();
                
                switch (action) {
                    case 'reset-health':
                        batchResetHealth(selectedIds);
                        break;
                    case 'delete-selected':
                        batchDeleteConfigs(selectedIds);
                        break;
                    case 'export-selected':
                        batchExportConfigs(selectedIds);
                        break;
                    case 'recheck-health':
                        batchRecheckHealth(selectedIds);
                        break;
                    default:
                        showToast('Unknown action: ' + action, 'error');
                }
            }
            
            function batchResetHealth(postIds) {
                if (!confirm(`Reset health status to "Unknown" for ${postIds.length} post(s)?`)) {
                    return;
                }
                
                showToast('Resetting health status...', 'info');
                
                // Reset health for each selected post
                const promises = postIds.map(postId => {
                    return $.ajax({
                        url: config.restUrl + '/posts/' + postId + '/health',
                        method: 'DELETE',
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                        }
                    });
                });
                
                Promise.allSettled(promises).then(results => {
                    const successful = results.filter(r => r.status === 'fulfilled').length;
                    const failed = results.length - successful;
                    
                    if (successful > 0) {
                        showToast(`Health reset for ${successful} post(s)`, 'success');
                        loadPosts(); // Refresh the table
                    }
                    if (failed > 0) {
                        showToast(`Failed to reset health for ${failed} post(s)`, 'error');
                    }
                });
            }
            
            function batchDeleteConfigs(postIds) {
                if (!confirm(`Are you sure you want to delete configurations for ${postIds.length} post(s)?\n\nThis action cannot be undone.`)) {
                    return;
                }
                
                showToast('Deleting configurations...', 'info');
                
                const promises = postIds.map(postId => {
                    return $.ajax({
                        url: config.restUrl + '/posts/' + postId,
                        method: 'DELETE',
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                        }
                    });
                });
                
                Promise.allSettled(promises).then(results => {
                    const successful = results.filter(r => r.status === 'fulfilled').length;
                    const failed = results.length - successful;
                    
                    if (successful > 0) {
                        showToast(`Deleted ${successful} configuration(s)`, 'success');
                        loadPosts(); // Refresh the table
                    }
                    if (failed > 0) {
                        showToast(`Failed to delete ${failed} configuration(s)`, 'error');
                    }
                });
            }
            
            function batchExportConfigs(postIds) {
                showToast('Exporting configurations...', 'info');
                
                // Get configurations for selected posts
                const selectedPosts = postsData.filter(post => postIds.includes(post.post_id));
                
                const exportData = {
                    export_info: {
                        timestamp: new Date().toISOString(),
                        post_count: selectedPosts.length,
                        exported_by: 'SmartLink Updater WordPress Plugin'
                    },
                    configurations: selectedPosts
                };
                
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const filename = `smartlink-configs-${selectedPosts.length}-posts-${timestamp}.json`;
                
                // Create and download file
                const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                showToast(`Exported ${selectedPosts.length} configuration(s)`, 'success');
            }
            
            function batchRecheckHealth(postIds) {
                if (!confirm(`Re-check health status for ${postIds.length} post(s)?`)) {
                    return;
                }
                
                showToast('Re-checking health status...', 'info');
                
                const promises = postIds.map(postId => {
                    return $.ajax({
                        url: config.restUrl + '/posts/' + postId + '/health/check',
                        method: 'POST',
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader('X-WP-Nonce', config.nonce);
                        }
                    });
                });
                
                Promise.allSettled(promises).then(results => {
                    const successful = results.filter(r => r.status === 'fulfilled').length;
                    const failed = results.length - successful;
                    
                    if (successful > 0) {
                        showToast(`Health check completed for ${successful} post(s)`, 'success');
                        loadPosts(); // Refresh the table
                    }
                    if (failed > 0) {
                        showToast(`Health check failed for ${failed} post(s)`, 'error');
                    }
                });
            }
            
            // ========== FILTERING AND SEARCH ==========
            
            let filteredPostsData = [];
            
            function debounce(func, wait) {
                let timeout;
                return function executedFunction(...args) {
                    const later = function() {
                        clearTimeout(timeout);
                        func(...args);
                    };
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                };
            }
            
            function applyFilters() {
                const searchTerm = $('#search-posts').val().toLowerCase();
                const healthFilter = $('#filter-health').val();
                const extractorFilter = $('#filter-extractor').val();
                
                filteredPostsData = postsData.filter(function(post) {
                    // Search filter
                    if (searchTerm) {
                        const matchesId = post.post_id.toString().toLowerCase().includes(searchTerm);
                        const postTitle = $('#posts-table-body tr[data-post-id="' + post.post_id + '"] td:nth-child(3)').text().toLowerCase();
                        const matchesTitle = postTitle.includes(searchTerm);
                        if (!matchesId && !matchesTitle) return false;
                    }
                    
                    // Health filter
                    if (healthFilter && post.health_status !== healthFilter) {
                        return false;
                    }
                    
                    // Extractor filter
                    if (extractorFilter && (post.extractor || 'default') !== extractorFilter) {
                        return false;
                    }
                    
                    return true;
                });
                
                renderFilteredTable();
                updateFilteredStats();
                
                // Re-apply sorting if active
                if (currentSort.column) {
                    applySorting();
                }
            }
            
            function renderFilteredTable() {
                const tbody = $('#posts-table-body');
                const allRows = tbody.find('tr');
                
                // Hide all rows first
                allRows.hide();
                
                // Show matching rows
                filteredPostsData.forEach(function(post) {
                    tbody.find('tr[data-post-id="' + post.post_id + '"]').show();
                });
                
                // Show "no results" message if needed
                if (filteredPostsData.length === 0) {
                    const existingNoResults = tbody.find('.no-results-row');
                    if (existingNoResults.length === 0) {
                        tbody.append('<tr class="no-results-row"><td colspan="9" style="text-align: center; padding: 40px; color: #666;">No posts match the current filters.</td></tr>');
                    }
                    existingNoResults.show();
                } else {
                    tbody.find('.no-results-row').hide();
                }
                
                updateSelectedCount();
            }
            
            function updateFilteredStats() {
                const total = filteredPostsData.length;
                const healthy = filteredPostsData.filter(p => p.health_status === 'healthy').length;
                const warning = filteredPostsData.filter(p => p.health_status === 'warning').length;
                const critical = filteredPostsData.filter(p => p.health_status === 'critical').length;
                
                // Update stats with filtered data
                $('#stat-total-posts').text(total);
                // Note: We'll update these when the filtering is more integrated with health stats
            }
            
            function clearFilters() {
                $('#search-posts').val('');
                $('#filter-health').val('');
                $('#filter-extractor').val('');
                
                // Clear sorting
                $('.sort-indicator').removeClass('asc desc');
                currentSort = { column: null, direction: null };
                
                // Show all rows and remove no-results message
                $('#posts-table-body tr').show();
                $('#posts-table-body .no-results-row').remove();
                
                // Reset filtered data to all data and re-render to original order
                filteredPostsData = [...postsData];
                renderPostsTable(postsData);
                updateStatistics(postsData);
            }
            
            function populateExtractorFilter() {
                const extractors = [...new Set(postsData.map(post => post.extractor || 'default'))];
                const select = $('#filter-extractor');
                
                // Clear existing options except first
                select.find('option:not(:first)').remove();
                
                // Add extractor options
                extractors.forEach(function(extractor) {
                    select.append(`<option value="${extractor}">${extractor}</option>`);
                });
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
            
            <!-- Statistics Dashboard -->
            <div class="smartlink-stats-container" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                <div class="stat-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Total Posts</div>
                            <div id="stat-total-posts" style="font-size: 32px; font-weight: 700; line-height: 1.2;">-</div>
                        </div>
                        <span class="dashicons dashicons-list-view" style="font-size: 48px; width: 48px; height: 48px; opacity: 0.3; line-height: 48px;"></span>
                    </div>
                </div>
                
                <div class="stat-card" style="background: linear-gradient(135deg, #55efc4 0%, #00b894 100%); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Active Updates</div>
                            <div id="stat-active-updates" style="font-size: 32px; font-weight: 700; line-height: 1.2;">0</div>
                        </div>
                        <span class="dashicons dashicons-update spin-icon" style="font-size: 48px; width: 48px; height: 48px; opacity: 0.3; line-height: 48px;"></span>
                    </div>
                </div>
                
                <div class="stat-card" style="background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Success Rate</div>
                            <div id="stat-success-rate" style="font-size: 32px; font-weight: 700; line-height: 1.2;">-</div>
                        </div>
                        <span class="dashicons dashicons-chart-line" style="font-size: 48px; width: 48px; height: 48px; opacity: 0.3; line-height: 48px;"></span>
                    </div>
                </div>
                
                <div class="stat-card" style="background: linear-gradient(135deg, #ff7675 0%, #d63031 100%); color: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(214, 48, 49, 0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">Failed Updates</div>
                            <div id="stat-failed-updates" style="font-size: 32px; font-weight: 700; line-height: 1.2;">0</div>
                        </div>
                        <span class="dashicons dashicons-warning" style="font-size: 48px; width: 48px; height: 48px; opacity: 0.3; line-height: 48px;"></span>
                    </div>
                </div>
            </div>
            
            <!-- Search and Filters -->
            <div class="smartlink-filters-container" style="background: white; padding: 20px; border-radius: 12px; margin: 20px 0; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); display: flex; gap: 20px; flex-wrap: wrap; align-items: center;">
                <div class="filter-group" style="display: flex; gap: 10px; align-items: center;">
                    <label for="search-posts" style="font-weight: 600; color: #333;">Search:</label>
                    <input type="text" id="search-posts" placeholder="Search by Post ID or Title..." style="padding: 8px 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 14px; min-width: 250px; transition: border-color 0.3s;">
                </div>
                <div class="filter-group" style="display: flex; gap: 10px; align-items: center;">
                    <label for="filter-health" style="font-weight: 600; color: #333;">Health:</label>
                    <select id="filter-health" class="smartlink-select" style="padding: 8px 12px; border: 2px solid #ddd; border-radius: 6px;">
                        <option value="">All Health States</option>
                        <option value="healthy">Healthy</option>
                        <option value="warning">Warning</option>
                        <option value="critical">Critical</option>
                        <option value="unknown">Unknown</option>
                    </select>
                </div>
                <div class="filter-group" style="display: flex; gap: 10px; align-items: center;">
                    <label for="filter-extractor" style="font-weight: 600; color: #333;">Extractor:</label>
                    <select id="filter-extractor" class="smartlink-select" style="padding: 8px 12px; border: 2px solid #ddd; border-radius: 6px;">
                        <option value="">All Extractors</option>
                        <!-- Options will be populated dynamically -->
                    </select>
                </div>
                <div class="filter-group" style="margin-left: auto;">
                    <button type="button" id="clear-filters" class="button" style="background: #f1f1f1; color: #666; border: 1px solid #ddd;">Clear Filters</button>
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
                    
                    <!-- Batch Operations Dropdown -->
                    <div class="batch-operations-dropdown" style="position: relative; display: inline-block; margin-left: 10px;">
                        <button type="button" id="batch-operations-btn" class="button" disabled>
                            <span class="dashicons dashicons-admin-tools"></span>
                            More Actions
                            <span class="dashicons dashicons-arrow-down-alt2" style="font-size: 12px; margin-left: 4px;"></span>
                        </button>
                        <div id="batch-operations-menu" class="batch-dropdown-menu" style="display: none;">
                            <button type="button" class="batch-operation-item" data-action="reset-health">
                                <span class="dashicons dashicons-heart"></span>
                                Reset Health for Selected
                            </button>
                            <button type="button" class="batch-operation-item" data-action="delete-selected">
                                <span class="dashicons dashicons-trash"></span>
                                Delete Selected Configs
                            </button>
                            <button type="button" class="batch-operation-item" data-action="export-selected">
                                <span class="dashicons dashicons-download"></span>
                                Export Selected Configs
                            </button>
                            <button type="button" class="batch-operation-item" data-action="recheck-health">
                                <span class="dashicons dashicons-editor-help"></span>
                                Re-check Health Status
                            </button>
                        </div>
                    </div>
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
                            <th scope="col" class="manage-column column-cb check-column">
                                <input type="checkbox" id="select-all-posts">
                            </th>
                            <th scope="col" class="manage-column sortable-header" data-sort="post_id">
                                Post ID <span class="sort-indicator"></span>
                            </th>
                            <th scope="col" class="manage-column column-title sortable-header" data-sort="title">
                                Title <span class="sort-indicator"></span>
                            </th>
                            <th scope="col" class="manage-column sortable-header" data-sort="extractor">
                                Extractor <span class="sort-indicator"></span>
                            </th>
                            <th scope="col" class="manage-column sortable-header" data-sort="health_status">
                                Health <span class="sort-indicator"></span>
                            </th>
                            <th scope="col" class="manage-column sortable-header" data-sort="updated_at">
                                Last Updated <span class="sort-indicator"></span>
                            </th>
                            <th scope="col" class="manage-column">Status</th>
                            <th scope="col" class="manage-column">Progress</th>
                            <th scope="col" class="manage-column column-actions">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="posts-table-body">
                        <tr>
                            <td colspan="9" style="text-align: center; padding: 40px;">
                                <span class="spinner is-active"></span>
                                Loading posts...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <!-- Logs Modal -->
            <div id="logs-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 1200px;">
                    <div class="smartlink-modal-header">
                        <h2>
                            <span class="dashicons dashicons-media-text"></span>
                            Update Logs: Post <span id="log-post-id"></span>
                        </h2>
                        <button type="button" class="close-modal">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                    
                    <!-- Log Controls -->
                    <div class="log-controls" style="padding: 15px 30px; border-bottom: 1px solid #e0e0e0; background: #fafafa; display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                        <div class="control-group" style="display: flex; gap: 8px; align-items: center;">
                            <label for="log-level-filter" style="font-weight: 600; color: #333;">Filter Level:</label>
                            <select id="log-level-filter" style="padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px;">
                                <option value="">All Levels</option>
                                <option value="DEBUG">Debug</option>
                                <option value="INFO">Info</option>
                                <option value="WARNING">Warning</option>
                                <option value="ERROR">Error</option>
                            </select>
                        </div>
                        
                        <div class="control-group" style="display: flex; gap: 8px; align-items: center;">
                            <label style="display: flex; align-items: center; gap: 6px; font-weight: 600; color: #333;">
                                <input type="checkbox" id="auto-scroll-logs" checked>
                                Auto-scroll to bottom
                            </label>
                        </div>
                        
                        <div class="control-group" style="display: flex; gap: 8px; align-items: center;">
                            <label style="display: flex; align-items: center; gap: 6px; font-weight: 600; color: #333;">
                                <input type="checkbox" id="wrap-lines-logs">
                                Wrap long lines
                            </label>
                        </div>
                        
                        <div class="control-group" style="margin-left: auto;">
                            <button type="button" id="clear-log-display" class="button" title="Clear display (keeps original logs)">
                                <span class="dashicons dashicons-dismiss"></span>
                                Clear Display
                            </button>
                        </div>
                    </div>
                    
                    <div class="smartlink-modal-body">
                        <div id="log-content" class="enhanced-log-content">
                            <div class="log-loading">
                                <span class="spinner is-active"></span>
                                Loading logs...
                            </div>
                        </div>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button close-modal">Close</button>
                        <button type="button" class="button" id="refresh-logs">
                            <span class="dashicons dashicons-image-rotate"></span>
                            Refresh
                        </button>
                        <button type="button" class="button button-primary" id="export-logs">
                            <span class="dashicons dashicons-download"></span>
                            Export Logs
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Edit Config Modal -->
            <div id="edit-config-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 700px;">
                    <div class="smartlink-modal-header">
                        <h2>Edit Configuration: Post <span id="edit-post-id"></span></h2>
                        <button type="button" class="close-edit-modal">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                    <div class="smartlink-modal-body">
                        <form id="edit-config-form">
                            <table class="form-table">
                                <tr>
                                    <th scope="row">
                                        <label for="edit-extractor">Extractor</label>
                                    </th>
                                    <td>
                                        <select id="edit-extractor" name="extractor" class="regular-text">
                                            <option value="">Auto-detect</option>
                                            <option value="simplegameguide">SimpleGameGuide</option>
                                            <option value="mosttechs">MostTechs</option>
                                            <option value="default">Default</option>
                                        </select>
                                        <p class="description">Choose the extractor to use for this post</p>
                                    </td>
                                </tr>
                                <tr>
                                    <th scope="row">
                                        <label for="edit-source-url">Source URL</label>
                                    </th>
                                    <td>
                                        <input type="url" id="edit-source-url" name="source_url" class="regular-text" placeholder="https://example.com/links/" />
                                        <p class="description">The URL to extract links from</p>
                                    </td>
                                </tr>
                                <tr>
                                    <th scope="row">
                                        <label for="edit-timezone">Timezone</label>
                                    </th>
                                    <td>
                                        <input type="text" id="edit-timezone" name="timezone" class="regular-text" placeholder="Asia/Kolkata" />
                                        <p class="description">Timezone for date parsing</p>
                                    </td>
                                </tr>
                            </table>
                        </form>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button close-edit-modal">Cancel</button>
                        <button type="button" class="button button-primary" id="save-config-btn">
                            <span class="dashicons dashicons-saved"></span>
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- View History Modal -->
            <div id="history-modal" class="smartlink-modal" style="display: none;">
                <div class="smartlink-modal-content" style="max-width: 900px;">
                    <div class="smartlink-modal-header">
                        <h2>Update History: Post <span id="history-post-id"></span></h2>
                        <button type="button" class="close-history-modal">
                            <span class="dashicons dashicons-no-alt"></span>
                        </button>
                    </div>
                    <div class="smartlink-modal-body">
                        <div id="history-content" class="history-content">
                            <span class="spinner is-active"></span>
                            Loading update history...
                        </div>
                    </div>
                    <div class="smartlink-modal-footer">
                        <button type="button" class="button close-history-modal">Close</button>
                        <button type="button" class="button" id="refresh-history">
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
        
        // Get single post config endpoint
        register_rest_route('smartlink/v1', '/post/(?P<post_id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'handle_get_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Update post config endpoint
        register_rest_route('smartlink/v1', '/post/(?P<post_id>\d+)', array(
            'methods' => 'PUT',
            'callback' => array($this, 'handle_update_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Delete post config endpoint
        register_rest_route('smartlink/v1', '/posts/(?P<post_id>\d+)', array(
            'methods' => 'DELETE',
            'callback' => array($this, 'handle_delete_post_config_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Reset health endpoint
        register_rest_route('smartlink/v1', '/posts/(?P<post_id>\d+)/health', array(
            'methods' => 'DELETE',
            'callback' => array($this, 'handle_reset_health_rest'),
            'permission_callback' => function() {
                return current_user_can('edit_posts');
            }
        ));
        
        // Recheck health endpoint
        register_rest_route('smartlink/v1', '/posts/(?P<post_id>\d+)/health/check', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_recheck_health_rest'),
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
     * Handle get post config REST request (server-side proxy)
     */
    public function handle_get_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API to get config
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
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
     * Handle update post config REST request (server-side proxy)
     */
    public function handle_update_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        $body = $request->get_json_params();
        
        if (empty($body)) {
            return new WP_Error('invalid_data', 'No data provided', array('status' => 400));
        }
        
        // Call Cloud Run API to update config
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
        $response = wp_remote_request($api_url, array(
            'method' => 'PUT',
            'timeout' => 30,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode($body)
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle delete post config REST request (server-side proxy)
     */
    public function handle_delete_post_config_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API to delete config
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id);
        
        $response = wp_remote_request($api_url, array(
            'method' => 'DELETE',
            'timeout' => 10
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle reset health REST request (server-side proxy)
     */
    public function handle_reset_health_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API to reset health
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id) . '/health/reset';
        
        $response = wp_remote_post($api_url, array(
            'timeout' => 10,
            'headers' => array('Content-Type' => 'application/json'),
            'body' => json_encode(array('health_status' => 'unknown'))
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
        return rest_ensure_response($data);
    }
    
    /**
     * Handle recheck health REST request (server-side proxy)
     */
    public function handle_recheck_health_rest($request) {
        $post_id = $request->get_param('post_id');
        
        // Call Cloud Run API to recheck health
        $api_url = $this->api_base_url . '/config/post/' . intval($post_id) . '/health/check';
        
        $response = wp_remote_post($api_url, array(
            'timeout' => 30,
            'headers' => array('Content-Type' => 'application/json')
        ));
        
        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message(), array('status' => 500));
        }
        
        $response_body = wp_remote_retrieve_body($response);
        $data = json_decode($response_body, true);
        
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
