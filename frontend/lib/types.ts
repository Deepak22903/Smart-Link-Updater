export type UpdateStatus = "queued" | "running" | "success" | "no_changes" | "partial" | "failed";
export type HealthStatus = "healthy" | "warning" | "failing" | "unknown";
export type ExtractionMode = "links" | "promo_codes" | "both";
export type AlertType = "structure_changed" | "zero_links" | "low_confidence" | "link_count_drop";
export type Severity = "info" | "warning" | "critical";

export interface PostListItem {
  post_id: number;
  content_slug: string;
  source_urls: string[];
  timezone: string;
  extractor: string;
  extraction_mode: ExtractionMode;
  health_status: HealthStatus;
  last_updated: string | null;
  site_post_ids: Record<string, number>;
  auto_update_sites: string[];
  use_custom_button_title: boolean;
  custom_button_title: string | null;
  days_to_keep: number;
  send_notifications: boolean;
}

export interface PostUpdateState {
  post_id: number;
  status: UpdateStatus;
  progress: number;
  message: string;
  links_found: number;
  links_added: number;
  error: string | null;
}

export interface BatchUpdateStatus {
  request_id: string;
  overall_status: UpdateStatus;
  total_posts: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  initiator: string;
  posts: Record<string, PostUpdateState>;
}

export interface BatchHistoryItem {
  request_id: string;
  created_at: string;
  completed_at: string | null;
  overall_status: UpdateStatus;
  initiator: string;
  total_posts: number;
  completed_posts: number;
  successful_posts: number;
  failed_posts: number;
  no_changes_posts: number;
}

export interface Alert {
  _id: string;
  alert_type: AlertType;
  source_url: string;
  severity: Severity;
  message: string;
  timestamp: string;
  notified: boolean;
}

export type PipelinePhase = "queued" | "scraping" | "extracting" | "deduplicating" | "updating_wp" | "done" | "failed";

export interface PipelinePost {
  post_id: number;
  content_slug: string;
  phase: PipelinePhase;
  progress: number;
  error?: string;
}

export interface ActiveBatch {
  request_id: string;
  total_posts: number;
  completed_posts: number;
  elapsed_seconds: number;
  posts: PipelinePost[];
}

export interface SiteConfig {
  base_url: string;
  username: string;
  display_name: string;
  button_style: string;
  app_password?: string;
}

export interface CronSettings {
  enabled: boolean;
  schedule: string;
  target_sites: string[];
}

export interface AnalyticsDashboard {
  period_days: number;
  total_updates: number;
  successful_updates: number;
  failed_updates: number;
  success_rate: number;
  total_links_added: number;
  active_posts: number;
  avg_links_per_update: number;
}

export interface TimelineDataPoint {
  date: string;
  successful: number;
  failed: number;
  total_links: number;
  success_rate: number;
}

export interface HourlyDataPoint {
  hour: number;
  total_updates: number;
  successful: number;
  failed: number;
}

export interface LinksTrendDataPoint {
  date: string;
  total_links: number;
  by_site: Record<string, number>;
}

export interface PostPerformance {
  post_id: number;
  content_slug: string;
  total_updates: number;
  successful_updates: number;
  success_rate: number;
  total_links_added: number;
  avg_links_per_update: number;
}

export interface SourcePerformance {
  source_url: string;
  total_extractions: number;
  successful_extractions: number;
  success_rate: number;
  health: HealthStatus;
  consecutive_failures: number;
  last_success: string | null;
}

export interface ExtractorPerformance {
  extractor: string;
  posts_using: number;
  total_links: number;
  avg_links_per_post: number;
}

export interface SitePerformance {
  site_key: string;
  display_name: string;
  links_added: number;
  posts_updated: number;
  avg_links_per_post: number;
}
