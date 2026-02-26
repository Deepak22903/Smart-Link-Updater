import type {
  PostListItem,
  BatchHistoryItem,
  Alert,
  SiteConfig,
  AnalyticsDashboard,
  ActiveBatch,
  TimelineDataPoint,
  HourlyDataPoint,
  LinksTrendDataPoint,
  PostPerformance,
  SourcePerformance,
  ExtractorPerformance,
  SitePerformance,
  CronSettings,
} from "./types";

export const mockPosts: PostListItem[] = [
  {
    post_id: 1,
    content_slug: "coin-master-free-spins",
    source_urls: ["https://simplegameguide.com/coin-master-free-spins/"],
    timezone: "UTC",
    extractor: "simplegameguide",
    extraction_mode: "links",
    health_status: "healthy",
    last_updated: "2026-02-26T08:30:00Z",
    site_post_ids: { minecraft: 1042, casino: 2031 },
    auto_update_sites: ["minecraft", "casino"],
    use_custom_button_title: false,
    custom_button_title: null,
    days_to_keep: 5,
    send_notifications: true,
  },
  {
    post_id: 2,
    content_slug: "travel-town-energy",
    source_urls: ["https://mosttechs.com/travel-town-free-energy/"],
    timezone: "UTC",
    extractor: "mosttechs",
    extraction_mode: "links",
    health_status: "healthy",
    last_updated: "2026-02-26T07:15:00Z",
    site_post_ids: { minecraft: 1055, gameblog: 3012 },
    auto_update_sites: ["minecraft", "gameblog"],
    use_custom_button_title: true,
    custom_button_title: "Claim Free Energy",
    days_to_keep: 3,
    send_notifications: true,
  },
  {
    post_id: 3,
    content_slug: "wsop-free-chips",
    source_urls: ["https://wsop.com/free-chips-promo/"],
    timezone: "America/New_York",
    extractor: "wsop",
    extraction_mode: "both",
    health_status: "warning",
    last_updated: "2026-02-25T22:00:00Z",
    site_post_ids: { casino: 2044 },
    auto_update_sites: ["casino"],
    use_custom_button_title: false,
    custom_button_title: null,
    days_to_keep: 7,
    send_notifications: true,
  },
  {
    post_id: 4,
    content_slug: "monopoly-go-dice",
    source_urls: ["https://techyhigher.com/monopoly-go-free-dice/"],
    timezone: "UTC",
    extractor: "techyhigher",
    extraction_mode: "links",
    health_status: "healthy",
    last_updated: "2026-02-26T06:45:00Z",
    site_post_ids: { minecraft: 1070, casino: 2050, gameblog: 3020 },
    auto_update_sites: ["minecraft", "casino", "gameblog"],
    use_custom_button_title: false,
    custom_button_title: null,
    days_to_keep: 5,
    send_notifications: false,
  },
  {
    post_id: 5,
    content_slug: "pet-master-spins",
    source_urls: ["https://gamesbie.com/pet-master-free-spins/"],
    timezone: "UTC",
    extractor: "gamesbie",
    extraction_mode: "links",
    health_status: "failing",
    last_updated: "2026-02-24T14:00:00Z",
    site_post_ids: { minecraft: 1083 },
    auto_update_sites: ["minecraft"],
    use_custom_button_title: true,
    custom_button_title: "Get Free Spins",
    days_to_keep: 4,
    send_notifications: true,
  },
  {
    post_id: 6,
    content_slug: "island-king-spins",
    source_urls: ["https://coinscrazy.com/island-king-free-spins/"],
    timezone: "Asia/Kolkata",
    extractor: "coinscrazy",
    extraction_mode: "links",
    health_status: "healthy",
    last_updated: "2026-02-26T09:00:00Z",
    site_post_ids: { minecraft: 1091, casino: 2062 },
    auto_update_sites: ["minecraft", "casino"],
    use_custom_button_title: false,
    custom_button_title: null,
    days_to_keep: 5,
    send_notifications: true,
  },
];

export const mockSites: Record<string, SiteConfig> = {
  minecraft: {
    base_url: "https://minecraftkey.com",
    username: "admin",
    display_name: "Minecraft Key",
    button_style: "gradient-blue",
  },
  casino: {
    base_url: "https://casinokey.net",
    username: "editor",
    display_name: "Casino Key",
    button_style: "gradient-green",
  },
  gameblog: {
    base_url: "https://gameblogpro.com",
    username: "publisher",
    display_name: "GameBlog Pro",
    button_style: "solid-orange",
  },
};

export const mockAlerts: Alert[] = [
  {
    _id: "alert-001",
    alert_type: "structure_changed",
    source_url: "https://gamesbie.com/pet-master-free-spins/",
    severity: "critical",
    message: "Page structure changed significantly. Extractor may need updating — 0 links found on last run.",
    timestamp: "2026-02-26T08:45:00Z",
    notified: false,
  },
  {
    _id: "alert-002",
    alert_type: "link_count_drop",
    source_url: "https://wsop.com/free-chips-promo/",
    severity: "warning",
    message: "Link count dropped from 12 to 3 compared to previous extraction.",
    timestamp: "2026-02-25T22:10:00Z",
    notified: true,
  },
  {
    _id: "alert-003",
    alert_type: "zero_links",
    source_url: "https://gamesbie.com/pet-master-free-spins/",
    severity: "critical",
    message: "Zero links extracted from source page. Possible extractor failure.",
    timestamp: "2026-02-24T14:05:00Z",
    notified: true,
  },
  {
    _id: "alert-004",
    alert_type: "low_confidence",
    source_url: "https://mosttechs.com/travel-town-free-energy/",
    severity: "info",
    message: "Extraction confidence score dropped to 72%. Review source page for changes.",
    timestamp: "2026-02-25T07:20:00Z",
    notified: false,
  },
  {
    _id: "alert-005",
    alert_type: "structure_changed",
    source_url: "https://coinscrazy.com/island-king-free-spins/",
    severity: "warning",
    message: "Minor DOM structure change detected. Links still extracted but verify accuracy.",
    timestamp: "2026-02-26T09:05:00Z",
    notified: false,
  },
  {
    _id: "alert-006",
    alert_type: "low_confidence",
    source_url: "https://techyhigher.com/monopoly-go-free-dice/",
    severity: "info",
    message: "Confidence score at 78% — slightly below threshold. Extraction succeeded but review recommended.",
    timestamp: "2026-02-25T12:30:00Z",
    notified: true,
  },
  {
    _id: "alert-007",
    alert_type: "link_count_drop",
    source_url: "https://simplegameguide.com/coin-master-free-spins/",
    severity: "warning",
    message: "Link count dropped from 8 to 4. Source page may have removed older links.",
    timestamp: "2026-02-24T18:00:00Z",
    notified: true,
  },
  {
    _id: "alert-008",
    alert_type: "low_confidence",
    source_url: "https://coinscrazy.com/island-king-free-spins/",
    severity: "info",
    message: "New HTML class names detected on link container. Extraction still functional.",
    timestamp: "2026-02-24T09:15:00Z",
    notified: true,
  },
];

export const mockBatchHistory: BatchHistoryItem[] = [
  {
    request_id: "batch-001",
    created_at: "2026-02-26T08:00:00Z",
    completed_at: "2026-02-26T08:12:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 4,
    failed_posts: 1,
    no_changes_posts: 1,
  },
  {
    request_id: "batch-002",
    created_at: "2026-02-26T02:00:00Z",
    completed_at: "2026-02-26T02:08:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 5,
    failed_posts: 0,
    no_changes_posts: 1,
  },
  {
    request_id: "batch-003",
    created_at: "2026-02-25T20:00:00Z",
    completed_at: "2026-02-25T20:15:00Z",
    overall_status: "failed",
    initiator: "manual",
    total_posts: 3,
    completed_posts: 3,
    successful_posts: 1,
    failed_posts: 2,
    no_changes_posts: 0,
  },
  {
    request_id: "batch-004",
    created_at: "2026-02-25T14:00:00Z",
    completed_at: "2026-02-25T14:10:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 6,
    failed_posts: 0,
    no_changes_posts: 0,
  },
  {
    request_id: "batch-005",
    created_at: "2026-02-25T08:00:00Z",
    completed_at: "2026-02-25T08:11:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 5,
    failed_posts: 0,
    no_changes_posts: 1,
  },
  {
    request_id: "batch-006",
    created_at: "2026-02-25T02:00:00Z",
    completed_at: "2026-02-25T02:09:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 4,
    failed_posts: 0,
    no_changes_posts: 2,
  },
  {
    request_id: "batch-007",
    created_at: "2026-02-24T20:00:00Z",
    completed_at: "2026-02-24T20:13:00Z",
    overall_status: "success",
    initiator: "api",
    total_posts: 4,
    completed_posts: 4,
    successful_posts: 3,
    failed_posts: 1,
    no_changes_posts: 0,
  },
  {
    request_id: "batch-008",
    created_at: "2026-02-24T14:00:00Z",
    completed_at: "2026-02-24T14:07:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 6,
    failed_posts: 0,
    no_changes_posts: 0,
  },
  {
    request_id: "batch-009",
    created_at: "2026-02-24T08:00:00Z",
    completed_at: "2026-02-24T08:14:00Z",
    overall_status: "failed",
    initiator: "manual",
    total_posts: 2,
    completed_posts: 2,
    successful_posts: 0,
    failed_posts: 2,
    no_changes_posts: 0,
  },
  {
    request_id: "batch-010",
    created_at: "2026-02-24T02:00:00Z",
    completed_at: "2026-02-24T02:10:00Z",
    overall_status: "success",
    initiator: "cron",
    total_posts: 6,
    completed_posts: 6,
    successful_posts: 5,
    failed_posts: 0,
    no_changes_posts: 1,
  },
];

export const mockAnalytics: AnalyticsDashboard = {
  period_days: 7,
  total_updates: 42,
  successful_updates: 36,
  failed_updates: 3,
  success_rate: 85.7,
  total_links_added: 284,
  active_posts: 6,
  avg_links_per_update: 6.8,
};

export const mockActiveBatch: ActiveBatch = {
  request_id: "batch-live-001",
  total_posts: 12,
  completed_posts: 7,
  elapsed_seconds: 83,
  posts: [
    { post_id: 1, content_slug: "coin-master-free-spins", phase: "done", progress: 100 },
    { post_id: 2, content_slug: "travel-town-energy", phase: "done", progress: 100 },
    { post_id: 3, content_slug: "wsop-free-chips", phase: "done", progress: 100 },
    { post_id: 4, content_slug: "monopoly-go-dice", phase: "done", progress: 100 },
    { post_id: 5, content_slug: "pet-master-spins", phase: "failed", progress: 100, error: "Extractor timeout after 30s" },
    { post_id: 6, content_slug: "island-king-spins", phase: "done", progress: 100 },
    { post_id: 7, content_slug: "board-kings-rolls", phase: "extracting", progress: 55 },
    { post_id: 8, content_slug: "piggy-go-dice", phase: "scraping", progress: 20 },
    { post_id: 9, content_slug: "match-masters-boost", phase: "queued", progress: 0 },
    { post_id: 10, content_slug: "bingo-blitz-credits", phase: "queued", progress: 0 },
    { post_id: 11, content_slug: "solitaire-grand", phase: "queued", progress: 0 },
    { post_id: 12, content_slug: "dice-dreams-rolls", phase: "done", progress: 100 },
  ],
};

export const unreadAlertCount = mockAlerts.filter((a) => !a.notified).length;

// ── Analytics Mock Data ──

function generateTimelineData(days: number): TimelineDataPoint[] {
  const data: TimelineDataPoint[] = [];
  const baseDate = new Date("2026-02-26");
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(baseDate);
    d.setDate(d.getDate() - i);
    const successful = Math.floor(Math.random() * 6) + 3;
    const failed = Math.random() > 0.75 ? Math.floor(Math.random() * 3) + 1 : 0;
    const total_links = successful * (Math.floor(Math.random() * 4) + 3);
    data.push({
      date: d.toISOString().split("T")[0],
      successful,
      failed,
      total_links,
      success_rate: Math.round((successful / (successful + failed)) * 100),
    });
  }
  return data;
}

export const mockTimelineData: TimelineDataPoint[] = generateTimelineData(30);

export const mockHourlyData: HourlyDataPoint[] = Array.from({ length: 24 }, (_, hour) => {
  const isActive = hour >= 6 && hour <= 22;
  const base = isActive ? Math.floor(Math.random() * 8) + 2 : Math.floor(Math.random() * 2);
  const failed = isActive && Math.random() > 0.8 ? 1 : 0;
  return { hour, total_updates: base + failed, successful: base, failed };
});

const siteKeys = Object.keys(mockSites);
export const mockLinksTrendData: LinksTrendDataPoint[] = mockTimelineData.map((d) => {
  const by_site: Record<string, number> = {};
  let remaining = d.total_links;
  siteKeys.forEach((key, idx) => {
    if (idx === siteKeys.length - 1) {
      by_site[key] = Math.max(0, remaining);
    } else {
      const portion = Math.floor(Math.random() * Math.ceil(remaining / 2)) + 1;
      by_site[key] = Math.min(portion, remaining);
      remaining -= by_site[key];
    }
  });
  return { date: d.date, total_links: d.total_links, by_site };
});

export const mockPostPerformance: PostPerformance[] = mockPosts.map((p) => {
  const updates = Math.floor(Math.random() * 20) + 10;
  const successRate = p.health_status === "failing" ? 45 + Math.random() * 20 : 80 + Math.random() * 18;
  const linksAdded = Math.floor(updates * (3 + Math.random() * 5));
  return {
    post_id: p.post_id,
    content_slug: p.content_slug,
    total_updates: updates,
    successful_updates: Math.round(updates * successRate / 100),
    success_rate: Math.round(successRate * 10) / 10,
    total_links_added: linksAdded,
    avg_links_per_update: Math.round((linksAdded / updates) * 10) / 10,
  };
});

export const mockSourcePerformance: SourcePerformance[] = mockPosts.flatMap((p) =>
  p.source_urls.map((url) => {
    const extractions = Math.floor(Math.random() * 25) + 8;
    const rate = p.health_status === "failing" ? 40 + Math.random() * 25 : 82 + Math.random() * 17;
    return {
      source_url: url,
      total_extractions: extractions,
      successful_extractions: Math.round(extractions * rate / 100),
      success_rate: Math.round(rate * 10) / 10,
      health: p.health_status === "unknown" ? "healthy" : p.health_status,
      consecutive_failures: p.health_status === "failing" ? 3 : p.health_status === "warning" ? 1 : 0,
      last_success: p.last_updated,
    } as SourcePerformance;
  })
);

export const mockExtractorPerformance: ExtractorPerformance[] = [
  { extractor: "simplegameguide", posts_using: 1, total_links: 187, avg_links_per_post: 6.2 },
  { extractor: "mosttechs", posts_using: 1, total_links: 142, avg_links_per_post: 5.1 },
  { extractor: "wsop", posts_using: 1, total_links: 98, avg_links_per_post: 4.3 },
  { extractor: "techyhigher", posts_using: 1, total_links: 165, avg_links_per_post: 5.7 },
  { extractor: "gamesbie", posts_using: 1, total_links: 52, avg_links_per_post: 2.8 },
  { extractor: "coinscrazy", posts_using: 1, total_links: 130, avg_links_per_post: 4.9 },
];

export const mockSitePerformance: SitePerformance[] = [
  { site_key: "minecraft", display_name: "Minecraft Key", links_added: 412, posts_updated: 5, avg_links_per_post: 5.4 },
  { site_key: "casino", display_name: "Casino Key", links_added: 298, posts_updated: 4, avg_links_per_post: 4.8 },
  { site_key: "gameblog", display_name: "GameBlog Pro", links_added: 137, posts_updated: 2, avg_links_per_post: 4.2 },
];

export const mockCronSettings: CronSettings = {
  enabled: true,
  schedule: "hourly",
  target_sites: ["all"],
};
