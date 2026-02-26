"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Zap,
  MoreHorizontal,
  Copy,
  Check,
  Trash2,
  Link2,
  Plus,
  Clock,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  RefreshCw,
  Globe,
} from "lucide-react";
import {
  theme,
  getStatusStyle,
  getHealthStyle,
  getExtractorStyle,
} from "@/lib/theme";
import { mockPosts, mockSites } from "@/lib/mock-data";
import type { ExtractionMode } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
} from "recharts";

// ──────────────────────────────────────────────────────
// Mock data specific to post detail
// ──────────────────────────────────────────────────────

const mockTodayLinks = [
  { title: "Coin Master Free 70 Spin Link", url: "https://rewards.coinmaster.com/spin70?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "50 Free Spins + 5M Coins", url: "https://rewards.coinmaster.com/spin50coins?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Coin Master 25 Spin Link Feb 26", url: "https://rewards.coinmaster.com/spin25-0226?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Free 10 Spins Daily Reward", url: "https://rewards.coinmaster.com/daily10?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Mega Spin Wheel Bonus", url: "https://rewards.coinmaster.com/mega-wheel?ref=sgguide&t=20260226", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Coin Master Free 15 Spin Link", url: "https://rewards.coinmaster.com/spin15?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Special Event 100 Spins", url: "https://rewards.coinmaster.com/event100?ref=sgguide&event=viking", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
  { title: "Free Coins 2M Link", url: "https://rewards.coinmaster.com/coins2m?ref=sgguide", source_url: "https://simplegameguide.com/coin-master-free-spins/", date: "2026-02-26" },
];

function generateHealthTimeline() {
  const data = [];
  const now = new Date("2026-02-26");
  for (let i = 29; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const failed = i === 22 || i === 8;
    data.push({
      date: d.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      links: failed ? 0 : Math.floor(Math.random() * 6) + 4,
      failed: failed ? 1 : 0,
    });
  }
  return data;
}

const healthTimeline = generateHealthTimeline();

const mockHistory = [
  { date: "2026-02-26", status: "success" as const, links: 8, confidence: 92, extractor: "simplegameguide", detail: mockTodayLinks.map((l) => l.title) },
  { date: "2026-02-25", status: "success" as const, links: 7, confidence: 89, extractor: "simplegameguide", detail: ["Free 60 Spin Link", "50 Spins + 3M Coins", "25 Spin Link Feb 25", "10 Spins Daily", "Mega Bonus 40 Spins", "Free Coins 1.5M", "Pet Event Spins"] },
  { date: "2026-02-24", status: "success" as const, links: 9, confidence: 94, extractor: "simplegameguide", detail: ["70 Spin Link", "50 Spins + 5M Coins", "25 Spin Link", "15 Spin Link", "10 Daily Spins", "Raid Event Bonus", "Free Coins 2M", "Village Master Spins", "Shield Bonus Link"] },
  { date: "2026-02-23", status: "failed" as const, links: 0, confidence: 0, extractor: "simplegameguide", detail: [], error: "Connection timeout after 30s" },
  { date: "2026-02-22", status: "success" as const, links: 6, confidence: 87, extractor: "simplegameguide", detail: ["Free 50 Spin Link", "30 Spins + 2M Coins", "25 Spin Link", "10 Daily Spins", "Free Coins 1M", "Event Spins"] },
  { date: "2026-02-21", status: "success" as const, links: 8, confidence: 91, extractor: "simplegameguide", detail: ["Free 70 Spin Link", "50 Spins + 4M Coins", "30 Spin Link", "25 Spin Link", "10 Daily Spins", "Mega Spin Bonus", "Free Coins 3M", "Attack Madness Spins"] },
  { date: "2026-02-20", status: "success" as const, links: 7, confidence: 88, extractor: "simplegameguide", detail: ["Free 60 Spin Link", "40 Spins + 2M Coins", "25 Spin Link", "15 Spin Link", "10 Daily Spins", "Free Coins 1.5M", "Balloon Frenzy Spins"] },
  { date: "2026-02-19", status: "success" as const, links: 5, confidence: 85, extractor: "simplegameguide", detail: ["Free 40 Spin Link", "25 Spin Link", "10 Daily Spins", "Free Coins 1M", "Event Spins"] },
  { date: "2026-02-18", status: "failed" as const, links: 0, confidence: 0, extractor: "simplegameguide", detail: [], error: "HTTP 503 Service Unavailable" },
  { date: "2026-02-17", status: "success" as const, links: 8, confidence: 93, extractor: "simplegameguide", detail: ["Free 70 Spin Link", "50 Spins + 5M Coins", "30 Spin Link", "25 Spin Link", "15 Spin Link", "10 Daily Spins", "Free Coins 2M", "Weekend Bonus Spins"] },
  { date: "2026-02-16", status: "success" as const, links: 6, confidence: 86, extractor: "simplegameguide", detail: ["Free 50 Spin Link", "30 Spins + 2M Coins", "25 Spin Link", "10 Daily Spins", "Free Coins 1M", "Event Spins"] },
  { date: "2026-02-15", status: "success" as const, links: 7, confidence: 90, extractor: "simplegameguide", detail: ["Free 60 Spin Link", "50 Spins + 3M Coins", "25 Spin Link", "15 Spin Link", "10 Daily Spins", "Free Coins 1.5M", "Valentine Event Spins"] },
  { date: "2026-02-14", status: "success" as const, links: 9, confidence: 95, extractor: "simplegameguide", detail: ["Valentine 100 Spin Link", "Free 70 Spin Link", "50 Spins + 5M Coins", "30 Spin Link", "25 Spin Link", "15 Spin Link", "10 Daily Spins", "Free Coins 3M", "Love Event Spins"] },
  { date: "2026-02-13", status: "success" as const, links: 6, confidence: 87, extractor: "simplegameguide", detail: ["Free 50 Spin Link", "30 Spins + 2M Coins", "25 Spin Link", "10 Daily Spins", "Free Coins 1M", "Raid Event Spins"] },
];

const mockFingerprints = {
  today: [
    "https://rewards.coinmaster.com/spin70?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/spin50coins?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/spin25-0226?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/daily10?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/mega-wheel?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/spin15?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/event100?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/coins2m?ref=sgguide|||2026-02-26",
    "https://rewards.coinmaster.com/spin70?ref=sgguide|||2026-02-25",
    "https://rewards.coinmaster.com/spin50coins?ref=sgguide|||2026-02-25",
    "https://rewards.coinmaster.com/daily10?ref=sgguide|||2026-02-25",
    "https://rewards.coinmaster.com/spin25?ref=sgguide|||2026-02-25",
  ],
  todayCount: 8,
  yesterdayCount: 7,
};

const mockLogs = [
  { ts: "2026-02-26T08:00:01Z", level: "INFO", msg: "Starting extraction for post coin-master-free-spins" },
  { ts: "2026-02-26T08:00:02Z", level: "INFO", msg: "Using extractor: simplegameguide" },
  { ts: "2026-02-26T08:00:03Z", level: "INFO", msg: "Fetching source URL: https://simplegameguide.com/coin-master-free-spins/" },
  { ts: "2026-02-26T08:00:05Z", level: "INFO", msg: "Page loaded successfully (HTTP 200, 45.2KB)" },
  { ts: "2026-02-26T08:00:06Z", level: "INFO", msg: "Parsing page content with simplegameguide extractor..." },
  { ts: "2026-02-26T08:00:07Z", level: "SUCCESS", msg: "Found 8 reward links on page" },
  { ts: "2026-02-26T08:00:07Z", level: "INFO", msg: "Generating fingerprints for deduplication..." },
  { ts: "2026-02-26T08:00:08Z", level: "INFO", msg: "5 new links identified (3 duplicates filtered)" },
  { ts: "2026-02-26T08:00:08Z", level: "INFO", msg: "Confidence score: 92%" },
  { ts: "2026-02-26T08:00:09Z", level: "INFO", msg: "Updating site: minecraft (post #1042)" },
  { ts: "2026-02-26T08:00:11Z", level: "SUCCESS", msg: "minecraft updated successfully" },
  { ts: "2026-02-26T08:00:12Z", level: "INFO", msg: "Updating site: casino (post #2031)" },
  { ts: "2026-02-26T08:00:14Z", level: "SUCCESS", msg: "casino updated successfully" },
  { ts: "2026-02-26T08:00:14Z", level: "INFO", msg: "Sending push notification for new links..." },
  { ts: "2026-02-26T08:00:15Z", level: "SUCCESS", msg: "Notification sent to 2 subscribers" },
  { ts: "2026-02-26T08:00:15Z", level: "WARNING", msg: "Link count lower than 7-day average (8 vs 7.3 avg)" },
  { ts: "2026-02-26T08:00:16Z", level: "INFO", msg: "Cleanup: removing links older than 5 days" },
  { ts: "2026-02-26T08:00:16Z", level: "INFO", msg: "Removed 3 expired links from storage" },
  { ts: "2026-02-26T08:00:17Z", level: "SUCCESS", msg: "Extraction completed successfully in 16.2s" },
  { ts: "2026-02-26T08:00:17Z", level: "INFO", msg: "Next scheduled run: 2026-02-26T14:00:00Z" },
];

const mockLogBatches = [
  { request_id: "batch-001", ts: "2026-02-26T08:00:00Z" },
  { request_id: "batch-002", ts: "2026-02-26T02:00:00Z" },
  { request_id: "batch-003", ts: "2026-02-25T20:00:00Z" },
  { request_id: "batch-004", ts: "2026-02-25T14:00:00Z" },
  { request_id: "batch-005", ts: "2026-02-25T08:00:00Z" },
];

// ──────────────────────────────────────────────────────
// Skeleton
// ──────────────────────────────────────────────────────

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-8 rounded" />
        <Skeleton className="h-8 w-64" />
      </div>
      <Skeleton className="h-10 w-96" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
}

// ──────────────────────────────────────────────────────
// Copy Button Helper
// ──────────────────────────────────────────────────────

function CopyButton({ text, className }: { text: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className={`inline-flex items-center justify-center rounded p-1 text-slate-400 transition-colors hover:text-slate-600 ${className ?? ""}`}
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

// ──────────────────────────────────────────────────────
// Main Component
// ──────────────────────────────────────────────────────

export function PostDetail({ postId }: { postId: number }) {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 400);
    return () => clearTimeout(t);
  }, []);

  const post = useMemo(
    () => mockPosts.find((p) => p.post_id === postId) ?? mockPosts[0],
    [postId]
  );

  const healthStyle = getHealthStyle(post.health_status);
  const extractorStyle = getExtractorStyle(post.extractor);

  if (loading) {
    return <DetailSkeleton />;
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* ── Header ── */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/posts"
              className="flex items-center justify-center rounded-lg border border-slate-200 p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {post.content_slug}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <Badge className={`${healthStyle.bg} ${healthStyle.text} border-0`}>
                  <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${healthStyle.dot}`} />
                  {post.health_status}
                </Badge>
                <Badge className={`${extractorStyle.bg} ${extractorStyle.text} border-0`}>
                  {post.extractor}
                </Badge>
                <Badge variant="outline" className="text-slate-500">
                  {post.extraction_mode}
                </Badge>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              className="bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-md hover:shadow-lg"
            >
              <Zap className="mr-1.5 h-4 w-4" />
              Update Now
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Link2 className="mr-2 h-4 w-4" /> Add Manual Links
                </DropdownMenuItem>
                <DropdownMenuItem className="text-red-600 focus:text-red-600">
                  <Trash2 className="mr-2 h-4 w-4" /> Delete Post
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* ── Tabs ── */}
        <Tabs defaultValue="overview">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="config">Config</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
          </TabsList>

          {/* ─── Tab: Overview ─── */}
          <TabsContent value="overview" className="space-y-6 pt-4">
            <OverviewTab post={post} />
          </TabsContent>

          {/* ─── Tab: History ─── */}
          <TabsContent value="history" className="space-y-6 pt-4">
            <HistoryTab />
          </TabsContent>

          {/* ─── Tab: Config ─── */}
          <TabsContent value="config" className="space-y-6 pt-4">
            <ConfigTab post={post} />
          </TabsContent>

          {/* ─── Tab: Logs ─── */}
          <TabsContent value="logs" className="space-y-6 pt-4">
            <LogsTab />
          </TabsContent>
        </Tabs>
      </div>
    </TooltipProvider>
  );
}

// ──────────────────────────────────────────────────────
// Tab: Overview
// ──────────────────────────────────────────────────────

function OverviewTab({ post }: { post: (typeof mockPosts)[0] }) {
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  const statusStyle = getStatusStyle("success");
  const confidenceColor =
    87 > 70 ? "text-emerald-600" : 87 > 40 ? "text-amber-600" : "text-red-600";
  const confidenceTrack =
    87 > 70 ? "#10b981" : 87 > 40 ? "#f59e0b" : "#ef4444";

  return (
    <>
      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Current Status
            </p>
            <div className="mt-2">
              <Badge className={`${statusStyle.bg} ${statusStyle.text} border-0 px-3 py-1 text-sm`}>
                SUCCESS
              </Badge>
            </div>
            <p className="mt-2 text-xs text-slate-400">Last run: 2h ago</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Confidence
            </p>
            <div className="mt-2 flex items-center gap-3">
              <div className="relative h-14 w-14">
                <svg className="h-14 w-14 -rotate-90" viewBox="0 0 56 56">
                  <circle
                    cx="28" cy="28" r="22" fill="none"
                    stroke="#e2e8f0" strokeWidth="5"
                  />
                  <circle
                    cx="28" cy="28" r="22" fill="none"
                    stroke={confidenceTrack} strokeWidth="5"
                    strokeDasharray={`${87 * 1.382} ${138.2 - 87 * 1.382}`}
                    strokeLinecap="round"
                  />
                </svg>
                <span className={`absolute inset-0 flex items-center justify-center text-sm font-bold ${confidenceColor}`}>
                  87%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Links Found
            </p>
            <p className="mt-1 text-3xl font-bold text-slate-900">8</p>
            <p className="text-xs text-slate-400">in last extraction</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Links Added
            </p>
            <p className="mt-1 text-3xl font-bold text-slate-900">5</p>
            <p className="text-xs text-slate-400">new today</p>
            <p className="text-xs text-slate-400">3 duplicates filtered</p>
          </CardContent>
        </Card>
      </div>

      {/* Today's Links Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{"Today's Links"}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[260px]">Title</TableHead>
                  <TableHead>URL</TableHead>
                  <TableHead>Source URL</TableHead>
                  <TableHead className="w-[100px]">Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockTodayLinks.map((link, i) => (
                  <TableRow key={i}>
                    <TableCell className="font-medium text-slate-800">
                      {link.title}
                    </TableCell>
                    <TableCell>
                      <div className="group flex items-center gap-1">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="max-w-[200px] truncate text-sm text-slate-600">
                              {link.url}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent className="max-w-[400px] break-all text-xs">
                            {link.url}
                          </TooltipContent>
                        </Tooltip>
                        <button
                          className="opacity-0 transition-opacity group-hover:opacity-100"
                          onClick={() => {
                            navigator.clipboard.writeText(link.url);
                            setCopiedUrl(link.url);
                            setTimeout(() => setCopiedUrl(null), 1500);
                          }}
                        >
                          {copiedUrl === link.url ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="h-3.5 w-3.5 text-slate-400" />
                          )}
                        </button>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="max-w-[180px] truncate text-sm text-slate-500">
                        {link.source_url.replace("https://", "").split("/")[0]}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-slate-500">
                      {link.date}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Health Timeline Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Health Timeline (30 days)</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={healthTimeline}>
              <defs>
                <linearGradient id="linksGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={theme.charts.success} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={theme.charts.success} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis
                dataKey="date" tick={{ fontSize: 11, fill: "#94a3b8" }}
                tickLine={false} axisLine={false} interval={4}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#94a3b8" }}
                tickLine={false} axisLine={false} width={30}
              />
              <RechartsTooltip
                contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0", fontSize: 12 }}
              />
              <Area
                type="monotone" dataKey="links" name="Links Found"
                stroke={theme.charts.success} fill="url(#linksGrad)"
                strokeWidth={2}
              />
              <Area
                type="monotone" dataKey="failed" name="Failed"
                stroke={theme.charts.failed} fill={theme.charts.failed}
                fillOpacity={0.3} strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Sites Summary */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Sites Summary</h3>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(mockSites)
            .filter(([key]) => post.site_post_ids[key] !== undefined)
            .map(([key, site], i) => (
              <Card key={key}>
                <CardContent className="flex items-center gap-3 py-4">
                  <span
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: theme.charts.sites[i % theme.charts.sites.length] }}
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-slate-800">
                      {site.display_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      Post #{post.site_post_ids[key]}
                    </p>
                    <p className="text-xs text-slate-400">Last updated: 1h ago</p>
                  </div>
                  <Badge
                    className={
                      post.auto_update_sites.includes(key)
                        ? "border-0 bg-emerald-100 text-emerald-700"
                        : "border-0 bg-slate-100 text-slate-500"
                    }
                  >
                    {post.auto_update_sites.includes(key) ? "Auto \u2713" : "Manual"}
                  </Badge>
                </CardContent>
              </Card>
            ))}
        </div>
      </div>
    </>
  );
}

// ──────────────────────────────────────────────────────
// Tab: History
// ──────────────────────────────────────────────────────

function HistoryTab() {
  const [expandedDay, setExpandedDay] = useState<string | null>(null);
  const [fingerprintsOpen, setFingerprintsOpen] = useState(false);

  return (
    <>
      {/* Extraction Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Extraction History (14 days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative ml-4 border-l-2 border-slate-200 pl-6">
            {mockHistory.map((entry) => {
              const isSuccess = entry.status === "success";
              const style = getStatusStyle(entry.status);
              const isExpanded = expandedDay === entry.date;

              return (
                <div key={entry.date} className="relative pb-6 last:pb-0">
                  {/* Timeline dot */}
                  <span
                    className={`absolute -left-[31px] top-1 h-3 w-3 rounded-full border-2 border-white ${style.dot}`}
                  />
                  <div className="flex items-start gap-3">
                    <span className="min-w-[100px] text-xs font-medium text-slate-500">
                      {new Date(entry.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </span>
                    <div className="flex-1">
                      <button
                        className="w-full text-left"
                        onClick={() =>
                          setExpandedDay(isExpanded ? null : entry.date)
                        }
                      >
                        <div className="flex items-center gap-2">
                          {isExpanded ? (
                            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
                          )}
                          {isSuccess ? (
                            <span className="text-sm text-slate-700">
                              {entry.links} links found &middot; Confidence:{" "}
                              {entry.confidence}% &middot;{" "}
                              <span className={`${getExtractorStyle(entry.extractor).text}`}>
                                {entry.extractor}
                              </span>
                            </span>
                          ) : (
                            <span className="text-sm text-red-600">
                              {"Failed: " + (entry as { error?: string }).error}
                            </span>
                          )}
                        </div>
                      </button>
                      {isExpanded && isSuccess && entry.detail.length > 0 && (
                        <ul className="mt-2 space-y-1 pl-5">
                          {entry.detail.map((title, i) => (
                            <li key={i} className="text-xs text-slate-500">
                              &bull; {title}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Fingerprints */}
      <Collapsible open={fingerprintsOpen} onOpenChange={setFingerprintsOpen}>
        <Card>
          <CollapsibleTrigger asChild>
            <CardHeader className="cursor-pointer select-none">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{"Today's Fingerprints"}</CardTitle>
                <ChevronDown
                  className={`h-4 w-4 text-slate-400 transition-transform ${
                    fingerprintsOpen ? "rotate-180" : ""
                  }`}
                />
              </div>
            </CardHeader>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <CardContent className="pt-0">
              <p className="mb-3 text-xs text-slate-500">
                {mockFingerprints.todayCount} fingerprints for today,{" "}
                {mockFingerprints.yesterdayCount} for yesterday
              </p>
              <div className="max-h-48 space-y-1 overflow-y-auto rounded-lg bg-slate-50 p-3">
                {mockFingerprints.today.map((fp, i) => (
                  <p key={i} className="truncate font-mono text-xs text-slate-500">
                    {fp}
                  </p>
                ))}
              </div>
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </>
  );
}

// ──────────────────────────────────────────────────────
// Tab: Config
// ──────────────────────────────────────────────────────

function ConfigTab({ post }: { post: (typeof mockPosts)[0] }) {
  const [sourceUrls, setSourceUrls] = useState(
    post.source_urls.map((url) => ({ url, extractor: post.extractor }))
  );
  const [siteMapping, setSiteMapping] = useState(
    Object.entries(mockSites).map(([key, site]) => ({
      key,
      name: site.display_name,
      postId: post.site_post_ids[key] ?? "",
      autoUpdate: post.auto_update_sites.includes(key),
    }))
  );
  const [daysToKeep, setDaysToKeep] = useState(post.days_to_keep);
  const [useCustomTitle, setUseCustomTitle] = useState(post.use_custom_button_title);
  const [customTitle, setCustomTitle] = useState(post.custom_button_title ?? "");
  const [buttonNumbering, setButtonNumbering] = useState("auto");
  const [promoTitle, setPromoTitle] = useState("Today's Free Links for {date}");
  const [extractionMode, setExtractionMode] = useState<ExtractionMode>(post.extraction_mode);
  const [notifications, setNotifications] = useState(post.send_notifications);
  const [hasChanges, setHasChanges] = useState(false);

  function markChanged() {
    setHasChanges(true);
  }

  return (
    <div className="space-y-8">
      {/* Identity */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Identity
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <Label className="text-xs text-slate-600">Content Slug</Label>
            <div className="mt-1 flex items-center gap-2">
              <Input value={post.content_slug} readOnly className="bg-slate-50 font-mono text-sm" />
              <CopyButton text={post.content_slug} />
            </div>
          </div>
          <div>
            <Label className="text-xs text-slate-600">Post ID (legacy)</Label>
            <p className="mt-2 font-mono text-sm text-slate-700">#{post.post_id}</p>
          </div>
        </div>
      </section>

      {/* Source URLs */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Source URLs
        </h3>
        <div className="space-y-3">
          {sourceUrls.map((src, i) => {
            const extStyle = getExtractorStyle(src.extractor);
            const health = post.health_status;
            const hStyle = getHealthStyle(health);
            return (
              <div key={i} className="flex items-center gap-2">
                <Input
                  value={src.url}
                  onChange={(e) => {
                    const next = [...sourceUrls];
                    next[i] = { ...next[i], url: e.target.value };
                    setSourceUrls(next);
                    markChanged();
                  }}
                  className="flex-1 font-mono text-sm"
                />
                <Select
                  value={src.extractor}
                  onValueChange={(v) => {
                    const next = [...sourceUrls];
                    next[i] = { ...next[i], extractor: v };
                    setSourceUrls(next);
                    markChanged();
                  }}
                >
                  <SelectTrigger className="w-[160px] text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="auto">Auto-detect</SelectItem>
                    {Object.keys(theme.extractors)
                      .filter((k) => k !== "default")
                      .map((ext) => {
                        const s = getExtractorStyle(ext);
                        return (
                          <SelectItem key={ext} value={ext}>
                            <span className={`${s.text} font-medium`}>{ext}</span>
                          </SelectItem>
                        );
                      })}
                  </SelectContent>
                </Select>
                <span className={`h-2.5 w-2.5 rounded-full ${hStyle.dot}`} />
                <button
                  className="rounded p-1.5 text-slate-400 transition-colors hover:bg-red-50 hover:text-red-500"
                  onClick={() => {
                    setSourceUrls(sourceUrls.filter((_, j) => j !== i));
                    markChanged();
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            );
          })}
          <Button
            variant="outline" size="sm"
            onClick={() => {
              setSourceUrls([...sourceUrls, { url: "", extractor: "auto" }]);
              markChanged();
            }}
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Source URL
          </Button>
        </div>
      </section>

      {/* Site Mapping */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Site Mapping
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {siteMapping.map((site, i) => (
            <div
              key={site.key}
              className="flex items-center gap-3 rounded-lg border border-slate-200 p-3"
            >
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: theme.charts.sites[i % theme.charts.sites.length] }}
              />
              <div className="flex-1">
                <Label className="text-xs font-medium text-slate-700">
                  {site.name}
                </Label>
                <Input
                  type="number"
                  value={site.postId}
                  onChange={(e) => {
                    const next = [...siteMapping];
                    next[i] = { ...next[i], postId: e.target.value };
                    setSiteMapping(next);
                    markChanged();
                  }}
                  className="mt-1 h-8 w-24 font-mono text-sm"
                  placeholder="Post ID"
                />
              </div>
              <div className="flex items-center gap-2">
                <Label className="text-xs text-slate-500">Auto</Label>
                <Switch
                  checked={site.autoUpdate}
                  onCheckedChange={(v) => {
                    const next = [...siteMapping];
                    next[i] = { ...next[i], autoUpdate: v };
                    setSiteMapping(next);
                    markChanged();
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Display Settings */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Display Settings
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <Label className="text-xs text-slate-600">Days to keep</Label>
            <Input
              type="number" min={1} max={30} value={daysToKeep}
              onChange={(e) => { setDaysToKeep(Number(e.target.value)); markChanged(); }}
              className="mt-1 w-24"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Switch checked={useCustomTitle} onCheckedChange={(v) => { setUseCustomTitle(v); markChanged(); }} />
              <Label className="text-xs text-slate-600">Custom button title</Label>
            </div>
            <Input
              value={customTitle} disabled={!useCustomTitle}
              onChange={(e) => { setCustomTitle(e.target.value); markChanged(); }}
              className="mt-1" placeholder="e.g. Claim Free Spins"
            />
          </div>
          <div>
            <Label className="text-xs text-slate-600">Button numbering</Label>
            <RadioGroup value={buttonNumbering} onValueChange={(v) => { setButtonNumbering(v); markChanged(); }} className="mt-2">
              <div className="flex items-center gap-2">
                <RadioGroupItem value="auto" id="btn-auto" />
                <Label htmlFor="btn-auto" className="text-sm text-slate-700">Auto</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="always" id="btn-always" />
                <Label htmlFor="btn-always" className="text-sm text-slate-700">Always</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="never" id="btn-never" />
                <Label htmlFor="btn-never" className="text-sm text-slate-700">Never</Label>
              </div>
            </RadioGroup>
          </div>
          <div>
            <Label className="text-xs text-slate-600">Promo section title</Label>
            <Input
              value={promoTitle}
              onChange={(e) => { setPromoTitle(e.target.value); markChanged(); }}
              className="mt-1"
            />
            <p className="mt-1 text-xs text-slate-400">
              {"Use {date} for dynamic date"}
            </p>
          </div>
        </div>
      </section>

      {/* Extraction Mode */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Extraction Mode
        </h3>
        <RadioGroup
          value={extractionMode}
          onValueChange={(v) => { setExtractionMode(v as ExtractionMode); markChanged(); }}
        >
          <div className="space-y-3">
            <div className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
              <RadioGroupItem value="links" id="mode-links" className="mt-0.5" />
              <div>
                <Label htmlFor="mode-links" className="text-sm font-medium text-slate-800">Links Only</Label>
                <p className="text-xs text-slate-500">Extract reward/game links</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
              <RadioGroupItem value="promo_codes" id="mode-promo" className="mt-0.5" />
              <div>
                <Label htmlFor="mode-promo" className="text-sm font-medium text-slate-800">Promo Codes Only</Label>
                <p className="text-xs text-slate-500">Extract promotional codes</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
              <RadioGroupItem value="both" id="mode-both" className="mt-0.5" />
              <div>
                <Label htmlFor="mode-both" className="text-sm font-medium text-slate-800">Both</Label>
                <p className="text-xs text-slate-500">Extract links and promo codes</p>
              </div>
            </div>
          </div>
        </RadioGroup>
      </section>

      {/* Notifications */}
      <section>
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
          Notifications
        </h3>
        <div className="flex items-center gap-3">
          <Switch checked={notifications} onCheckedChange={(v) => { setNotifications(v); markChanged(); }} />
          <div>
            <Label className="text-sm text-slate-700">Push notifications</Label>
            <p className="text-xs text-slate-400">Send push notification when new links are found</p>
          </div>
        </div>
      </section>

      {/* Save */}
      <div className="flex items-center gap-3 border-t border-slate-200 pt-6">
        <Button
          className="bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-md"
          disabled={!hasChanges}
        >
          Save Changes
        </Button>
        {hasChanges && (
          <span className="text-xs text-amber-600">Unsaved changes</span>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────
// Tab: Logs
// ──────────────────────────────────────────────────────

function LogsTab() {
  const [selectedBatch, setSelectedBatch] = useState(mockLogBatches[0].request_id);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const isLive = selectedBatch === mockLogBatches[0].request_id;

  function levelColor(level: string) {
    switch (level) {
      case "SUCCESS": return "text-emerald-400";
      case "WARNING": return "text-amber-400";
      case "ERROR": return "text-red-400";
      default: return "text-slate-400";
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-base">Log Viewer</CardTitle>
            {isLive && (
              <span className="flex items-center gap-1.5 text-xs text-emerald-600">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                Live
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedBatch} onValueChange={setSelectedBatch}>
              <SelectTrigger className="h-8 w-[240px] text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {mockLogBatches.map((b) => (
                  <SelectItem key={b.request_id} value={b.request_id}>
                    <span className="font-mono text-xs">{b.request_id}</span>
                    <span className="ml-2 text-slate-400">
                      {new Date(b.ts).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline" size="sm"
              onClick={() => {
                navigator.clipboard.writeText(
                  mockLogs.map((l) => `${l.ts} [${l.level}] ${l.msg}`).join("\n")
                );
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? <Check className="mr-1 h-3.5 w-3.5" /> : <Copy className="mr-1 h-3.5 w-3.5" />}
              {copied ? "Copied" : "Copy"}
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-1 h-3.5 w-3.5" /> Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-3">
          <Switch checked={autoScroll} onCheckedChange={setAutoScroll} />
          <Label className="text-xs text-slate-500">Auto-scroll to bottom</Label>
        </div>
        <div className="max-h-[420px] overflow-y-auto rounded-lg bg-slate-900 p-4 font-mono text-xs leading-relaxed">
          {mockLogs.map((log, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-blue-400/60 shrink-0">
                {new Date(log.ts).toLocaleTimeString("en-US", { hour12: false })}
              </span>
              <span className={`shrink-0 font-semibold ${levelColor(log.level)}`}>
                [{log.level}]
              </span>
              <span className="text-slate-300">{log.msg}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
