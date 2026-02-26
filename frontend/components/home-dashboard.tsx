"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Info,
  Loader2,
  Plus,
  Settings,
  Trash2,
  XCircle,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { theme, getStatusStyle, getExtractorStyle } from "@/lib/theme";
import {
  mockPosts,
  mockAlerts,
  mockBatchHistory,
  mockSites,
} from "@/lib/mock-data";

/* ─────────── helpers ─────────── */

function timeAgo(dateStr: string): string {
  const now = new Date("2026-02-26T09:30:00Z"); // stable reference time
  const diff = now.getTime() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const extractorKeys = [
  ...new Set(mockPosts.map((p) => p.extractor)),
];

/* ─────────── Cron Heartbeat ─────────── */

function CronHeartbeatCard() {
  const enabled = true;
  const healthColor = enabled
    ? theme.health.healthy.hex
    : theme.health.failing.hex;

  return (
    <Link href="/settings">
      <Card className="group cursor-pointer border-0 shadow-sm transition-shadow hover:shadow-md">
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Cron Heartbeat
              </p>
              <p className="text-xs text-muted-foreground">
                {"Last run 12m ago \u00B7 Next in 48m"}
              </p>
              <Badge
                className="border-0 text-xs"
                style={{
                  backgroundColor: healthColor + "18",
                  color: healthColor,
                }}
              >
                {enabled ? "Enabled" : "Disabled"}
              </Badge>
            </div>
            <span
              className="relative mt-1 flex h-3 w-3"
              aria-label={enabled ? "Cron enabled" : "Cron disabled"}
            >
              <span
                className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75"
                style={{ backgroundColor: healthColor }}
              />
              <span
                className="relative inline-flex h-3 w-3 rounded-full"
                style={{ backgroundColor: healthColor }}
              />
            </span>
          </div>
          <Settings className="mt-3 h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
        </CardContent>
      </Card>
    </Link>
  );
}

/* ─────────── System Health ring ─────────── */

function SystemHealthCard() {
  const totalSources = 25;
  const healthySources = 23;
  const pct = Math.round((healthySources / totalSources) * 100);
  const ringColor =
    pct > 80
      ? theme.health.healthy.hex
      : pct > 60
        ? theme.health.warning.hex
        : theme.health.failing.hex;

  const radius = 36;
  const circ = 2 * Math.PI * radius;
  const offset = circ - (pct / 100) * circ;

  return (
    <Card className="border-0 shadow-sm">
      <CardContent className="flex items-center gap-4 p-5">
        <svg width="80" height="80" viewBox="0 0 80 80" aria-hidden="true">
          <circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke="currentColor"
            className="text-muted/40"
            strokeWidth="6"
          />
          <circle
            cx="40"
            cy="40"
            r={radius}
            fill="none"
            stroke={ringColor}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            transform="rotate(-90 40 40)"
            className="transition-all duration-700"
          />
          <text
            x="40"
            y="38"
            textAnchor="middle"
            className="fill-foreground text-lg font-bold"
            style={{ fontSize: "16px", fontWeight: 700 }}
          >
            {pct}%
          </text>
          <text
            x="40"
            y="52"
            textAnchor="middle"
            className="fill-muted-foreground"
            style={{ fontSize: "8px" }}
          >
            healthy
          </text>
        </svg>
        <div>
          <p className="text-sm font-medium text-muted-foreground">
            Sources Healthy
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {healthySources}/{totalSources} sources OK
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

/* ─────────── Today's Stats ─────────── */

function TodaysStatsCard() {
  const linksToday = 14;
  const sitesCount = 3;
  const sparkData = [5, 8, 12, 7, 10, 14, 9];
  const max = Math.max(...sparkData);
  const svgW = 80;
  const svgH = 28;
  const points = sparkData
    .map((v, i) => {
      const x = (i / (sparkData.length - 1)) * svgW;
      const y = svgH - (v / max) * (svgH - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <Card className="border-0 shadow-sm">
      <CardContent className="p-5">
        <p className="text-sm font-medium text-muted-foreground">
          {"Today's Stats"}
        </p>
        <p className="mt-1 text-3xl font-bold text-foreground">{linksToday}</p>
        <p className="text-xs text-muted-foreground">
          links added today across {sitesCount} sites
        </p>
        <svg
          width={svgW}
          height={svgH}
          viewBox={`0 0 ${svgW} ${svgH}`}
          className="mt-2"
          aria-hidden="true"
        >
          <polyline
            points={points}
            fill="none"
            stroke={theme.charts.links}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </CardContent>
    </Card>
  );
}

/* ─────────── Active Batch ─────────── */

function ActiveBatchCard() {
  const isRunning = false;

  return (
    <Card className="border-0 shadow-sm">
      <CardContent className="p-5">
        <p className="text-sm font-medium text-muted-foreground">
          Active Batch
        </p>
        {isRunning ? (
          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Loader2 className="h-4 w-4 animate-spin" style={{ color: theme.brand.primary }} />
              Updating 5/12 posts...
            </div>
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted">
              <div
                className="absolute inset-0 h-full animate-pulse rounded-full bg-gradient-to-r"
                style={{
                  width: "42%",
                  backgroundImage: theme.brand.gradientCss,
                }}
              />
            </div>
          </div>
        ) : (
          <div className="mt-3">
            <p className="text-sm text-muted-foreground">No active batch</p>
            <Link
              href="/batches"
              className="mt-2 inline-flex items-center gap-1 text-xs font-medium hover:underline"
              style={{ color: theme.brand.primary }}
            >
              Run Now <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ─────────── Attention section ─────────── */

function AttentionSection() {
  const failedPosts = mockPosts.filter((p) => p.health_status === "failing");
  const structureAlerts = mockAlerts.filter(
    (a) => a.alert_type === "structure_changed" && a.severity !== "info"
  );
  const hasIssues = failedPosts.length > 0 || structureAlerts.length > 0;

  if (!hasIssues) {
    return (
      <div
        className="flex items-center gap-3 rounded-lg border p-4"
        style={{
          borderColor: theme.health.healthy.hex + "40",
          backgroundColor: theme.health.healthy.hex + "08",
        }}
      >
        <CheckCircle2
          className="h-5 w-5 shrink-0"
          style={{ color: theme.health.healthy.hex }}
        />
        <p className="text-sm font-medium text-foreground">
          All systems nominal — last checked 3m ago
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {failedPosts.length > 0 && (
        <div
          className={`flex items-center justify-between rounded-lg border-l-4 p-4 ${theme.status.failed.border}`}
          style={{ backgroundColor: theme.status.failed.hex + "08" }}
        >
          <div className="flex items-center gap-3">
            <XCircle className="h-5 w-5 shrink-0" style={{ color: theme.status.failed.hex }} />
            <p className="text-sm font-medium text-foreground">
              {failedPosts.length} posts failed extraction
            </p>
          </div>
          <Link
            href="/posts?status=failed"
            className="flex items-center gap-1 text-xs font-medium hover:underline"
            style={{ color: theme.status.failed.hex }}
          >
            View Posts <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      )}
      {structureAlerts.length > 0 && (
        <div
          className={`flex items-center justify-between rounded-lg border-l-4 p-4 ${theme.status.warning.border}`}
          style={{ backgroundColor: theme.status.warning.hex + "08" }}
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0" style={{ color: theme.status.warning.hex }} />
            <p className="text-sm font-medium text-foreground">
              {structureAlerts.length} source URL changed structure
            </p>
          </div>
          <Link
            href="/alerts"
            className="flex items-center gap-1 text-xs font-medium hover:underline"
            style={{ color: theme.status.warning.hex }}
          >
            View Alerts <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      )}
    </div>
  );
}

/* ─────────── Add Manual Links Dialog ─────────── */

function AddManualLinksDialog() {
  const [links, setLinks] = useState([{ title: "", url: "" }]);
  const siteKeys = Object.keys(mockSites);

  function addRow() {
    setLinks((prev) => [...prev, { title: "", url: "" }]);
  }
  function removeRow(idx: number) {
    setLinks((prev) => prev.filter((_, i) => i !== idx));
  }
  function updateRow(idx: number, field: "title" | "url", value: string) {
    setLinks((prev) =>
      prev.map((l, i) => (i === idx ? { ...l, [field]: value } : l))
    );
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Plus className="h-4 w-4" />
          Add Manual Links
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add Manual Links</DialogTitle>
          <DialogDescription>
            Manually add links to a post and push to target sites.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label>Post</Label>
            <Select>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a post..." />
              </SelectTrigger>
              <SelectContent>
                {mockPosts.map((p) => (
                  <SelectItem key={p.post_id} value={String(p.post_id)}>
                    {p.content_slug}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Date</Label>
            <Input type="date" defaultValue="2026-02-26" />
          </div>

          <div className="space-y-2">
            <Label>Links</Label>
            {links.map((link, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <Input
                  placeholder="Title"
                  value={link.title}
                  onChange={(e) => updateRow(idx, "title", e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="URL"
                  value={link.url}
                  onChange={(e) => updateRow(idx, "url", e.target.value)}
                  className="flex-1"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeRow(idx)}
                  disabled={links.length === 1}
                  className="shrink-0"
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">Remove link row</span>
                </Button>
              </div>
            ))}
            <Button variant="outline" size="sm" onClick={addRow} className="gap-1">
              <Plus className="h-3 w-3" /> Add Link
            </Button>
          </div>

          <div className="space-y-2">
            <Label>Target Sites</Label>
            <div className="flex flex-wrap gap-4">
              {siteKeys.map((key) => (
                <div key={key} className="flex items-center gap-2">
                  <Checkbox id={`site-${key}`} defaultChecked />
                  <label htmlFor={`site-${key}`} className="text-sm text-foreground">
                    {mockSites[key].display_name}
                  </label>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            className="bg-gradient-to-r text-white"
            style={{ backgroundImage: theme.brand.gradientCss }}
          >
            Submit
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* ─────────── Quick Actions ─────────── */

function QuickActions() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button
        className="gap-2 text-white shadow-md"
        style={{ backgroundImage: theme.brand.gradientCss }}
      >
        <Zap className="h-4 w-4" />
        Update All Posts
      </Button>

      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className="gap-2"
            style={{ borderColor: theme.brand.primary + "60", color: theme.brand.primary }}
          >
            Update by Extractor...
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-56 p-2">
          <div className="space-y-1">
            {extractorKeys.map((key) => {
              const style = getExtractorStyle(key);
              return (
                <button
                  key={key}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-foreground transition-colors hover:bg-accent"
                >
                  <Badge className={`border-0 text-xs ${style.bg} ${style.text}`}>
                    {key}
                  </Badge>
                </button>
              );
            })}
          </div>
        </PopoverContent>
      </Popover>

      <AddManualLinksDialog />
    </div>
  );
}

/* ─────────── Recent Batches ─────────── */

function RecentBatches() {
  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-semibold text-foreground">
          Recent Batches
        </CardTitle>
        <Link
          href="/batches"
          className="flex items-center gap-1 text-xs font-medium hover:underline"
          style={{ color: theme.brand.primary }}
        >
          View All <ArrowUpRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-2">
        {mockBatchHistory.slice(0, 5).map((batch) => {
          const statusStyle = getStatusStyle(batch.overall_status);
          return (
            <Link
              key={batch.request_id}
              href="/batches"
              className="flex items-center justify-between rounded-lg p-3 transition-colors hover:bg-accent"
            >
              <div className="flex items-center gap-3">
                <code className="font-mono text-xs text-muted-foreground">
                  {batch.request_id.slice(0, 12)}
                </code>
                <span className="text-xs text-muted-foreground">
                  {timeAgo(batch.created_at)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Badge
                  className={`border-0 text-xs ${statusStyle.bg} ${statusStyle.text}`}
                >
                  {batch.overall_status}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {batch.total_posts} posts
                </span>
                <Badge
                  className={`border-0 text-xs ${
                    batch.initiator === "cron"
                      ? "bg-muted text-muted-foreground"
                      : ""
                  }`}
                  style={
                    batch.initiator !== "cron"
                      ? {
                          backgroundColor: theme.brand.primary + "18",
                          color: theme.brand.primary,
                        }
                      : undefined
                  }
                >
                  {batch.initiator}
                </Badge>
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}

/* ─────────── Recent Alerts ─────────── */

function RecentAlerts() {
  const alertIcons: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
    critical: XCircle,
    warning: AlertTriangle,
    info: Info,
  };

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-base font-semibold text-foreground">
          Recent Alerts
        </CardTitle>
        <Link
          href="/alerts"
          className="flex items-center gap-1 text-xs font-medium hover:underline"
          style={{ color: theme.brand.primary }}
        >
          View All <ArrowUpRight className="h-3 w-3" />
        </Link>
      </CardHeader>
      <CardContent className="space-y-1">
        {mockAlerts.slice(0, 8).map((alert) => {
          const severityStyle = getStatusStyle(
            alert.severity === "critical" ? "failed" : alert.severity
          );
          const IconComp = alertIcons[alert.severity] || Info;
          return (
            <Link
              key={alert._id}
              href="/alerts"
              className="flex items-start gap-3 rounded-lg p-3 transition-colors hover:bg-accent"
            >
              <IconComp
                className="mt-0.5 h-4 w-4 shrink-0"
                style={{ color: severityStyle.hex }}
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {alert.message}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {timeAgo(alert.timestamp)}
                </p>
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}

/* ─────────── Loading skeleton ─────────── */

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-2 h-4 w-72" />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>
      <Skeleton className="h-16 rounded-lg" />
      <div className="flex gap-3">
        <Skeleton className="h-10 w-40" />
        <Skeleton className="h-10 w-44" />
        <Skeleton className="h-10 w-40" />
      </div>
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Skeleton className="h-80 rounded-lg" />
        <Skeleton className="h-80 rounded-lg" />
      </div>
    </div>
  );
}

/* ─────────── Main Dashboard ─────────── */

export function HomeDashboard() {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setLoaded(true), 400);
    return () => clearTimeout(t);
  }, []);

  if (!loaded) return <DashboardSkeleton />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground text-balance">
          Command Center
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          SmartLink Updater overview and quick actions
        </p>
      </div>

      {/* Top Status Strip */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CronHeartbeatCard />
        <SystemHealthCard />
        <TodaysStatsCard />
        <ActiveBatchCard />
      </div>

      {/* Attention Section */}
      <AttentionSection />

      {/* Quick Actions */}
      <QuickActions />

      {/* Recent Activity — 2-col on desktop */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <RecentBatches />
        <RecentAlerts />
      </div>
    </div>
  );
}
