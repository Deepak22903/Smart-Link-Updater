"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  XOctagon,
  AlertTriangle,
  Info,
  X,
  CheckCheck,
  Trash2,
  Copy,
  Check,
  PartyPopper,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { theme } from "@/lib/theme";
import { mockAlerts, mockPosts } from "@/lib/mock-data";
import type { Alert, Severity, AlertType } from "@/lib/types";

// ── Helpers ──

function relativeTime(dateStr: string): string {
  const now = new Date("2026-02-26T10:00:00Z");
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}

function getSeverityIcon(severity: Severity) {
  switch (severity) {
    case "critical":
      return <XOctagon className={`h-5 w-5 shrink-0 ${theme.status.failed.text}`} />;
    case "warning":
      return <AlertTriangle className={`h-5 w-5 shrink-0 ${theme.status.warning.text}`} />;
    case "info":
      return <Info className={`h-5 w-5 shrink-0 ${theme.status.info.text}`} />;
  }
}

function getSeverityBorder(severity: Severity): string {
  switch (severity) {
    case "critical":
      return theme.status.failed.border;
    case "warning":
      return theme.status.warning.border;
    case "info":
      return theme.status.info.border;
  }
}

function getSeverityTheme(severity: Severity) {
  switch (severity) {
    case "critical":
      return theme.status.failed;
    case "warning":
      return theme.status.warning;
    case "info":
      return theme.status.info;
  }
}

function alertTypeLabel(type: AlertType): string {
  const labels: Record<AlertType, string> = {
    structure_changed: "Source Structure Changed",
    zero_links: "Zero Links Detected",
    low_confidence: "Low Confidence Extraction",
    link_count_drop: "Link Count Drop",
  };
  return labels[type];
}

function findPostIdByUrl(url: string): number | null {
  const post = mockPosts.find((p) => p.source_urls.includes(url));
  return post ? post.post_id : null;
}

// ── Filter Toggle Button ──

function FilterToggle({
  label,
  count,
  active,
  onClick,
  severity,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
  severity?: Severity;
}) {
  const getBadgeColor = () => {
    if (!severity) return "bg-slate-500";
    switch (severity) {
      case "critical":
        return `bg-red-500`;
      case "warning":
        return `bg-amber-500`;
      case "info":
        return `bg-blue-500`;
    }
  };

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-slate-900 text-white"
          : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
      }`}
    >
      {label}
      <span
        className={`inline-flex items-center justify-center h-5 min-w-[20px] rounded-full px-1.5 text-xs font-semibold text-white ${
          active ? "bg-white/20" : getBadgeColor()
        }`}
      >
        {count}
      </span>
    </button>
  );
}

// ── Alert Card ──

function AlertCard({
  alert,
  onDismiss,
}: {
  alert: Alert;
  onDismiss: (id: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const severityBorder = getSeverityBorder(alert.severity);
  const isUnread = !alert.notified;
  const postId = findPostIdByUrl(alert.source_url);

  const handleCopyUrl = () => {
    navigator.clipboard.writeText(alert.source_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card
      className={`relative border-0 shadow-sm border-l-[3px] overflow-hidden ${severityBorder} ${
        isUnread ? "bg-blue-50/30" : ""
      }`}
    >
      {isUnread && (
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-[1px] h-2.5 w-2.5 rounded-full"
          style={{ backgroundColor: theme.status.info.hex }}
        />
      )}
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="mt-0.5">{getSeverityIcon(alert.severity)}</div>
          <div className="flex-1 min-w-0 space-y-1.5">
            <p className="text-sm font-semibold text-slate-800">
              {alertTypeLabel(alert.alert_type)}
            </p>
            <p className="text-sm text-slate-600 leading-relaxed">{alert.message}</p>
            <button
              onClick={handleCopyUrl}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-600 transition-colors max-w-full"
              title="Click to copy"
            >
              {copied ? (
                <Check className="h-3 w-3 text-emerald-500 shrink-0" />
              ) : (
                <Copy className="h-3 w-3 shrink-0" />
              )}
              <span className="truncate">{alert.source_url}</span>
            </button>
            <p className="text-xs text-slate-400">{relativeTime(alert.timestamp)}</p>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {postId && (
              <Button variant="outline" size="sm" className="text-xs h-7 gap-1" asChild>
                <Link href={`/posts/${postId}`}>
                  View Post
                  <span aria-hidden="true">&rarr;</span>
                </Link>
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-slate-400 hover:text-slate-600"
              onClick={() => onDismiss(alert._id)}
              aria-label="Dismiss alert"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Stats Bar ──

function AlertStatsBar({ alerts }: { alerts: Alert[] }) {
  const criticalCount = alerts.filter((a) => a.severity === "critical").length;
  const warningCount = alerts.filter((a) => a.severity === "warning").length;
  const infoCount = alerts.filter((a) => a.severity === "info").length;

  const stats = [
    { label: "Total", count: alerts.length, color: "text-slate-700", bg: "bg-white" },
    {
      label: "Critical",
      count: criticalCount,
      color: theme.status.failed.text,
      bg: theme.status.failed.bg,
    },
    {
      label: "Warning",
      count: warningCount,
      color: theme.status.warning.text,
      bg: theme.status.warning.bg,
    },
    {
      label: "Info",
      count: infoCount,
      color: theme.status.info.text,
      bg: theme.status.info.bg,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className={`rounded-lg border p-3 text-center ${s.bg}`}
        >
          <p className={`text-xs ${s.color}`}>{s.label}</p>
          <p className={`text-xl font-bold ${s.color}`}>{s.count}</p>
        </div>
      ))}
    </div>
  );
}

// ── Empty State ──

function EmptyAlerts() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="h-16 w-16 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
        <PartyPopper className={`h-8 w-8 ${theme.status.success.text}`} />
      </div>
      <h3 className="text-lg font-semibold text-slate-800">
        No alerts — everything is running smoothly
      </h3>
      <p className="text-sm text-slate-500 mt-1">
        Your sources and extractors are all healthy.
      </p>
    </div>
  );
}

// ── Alert Type Filter ──

type AlertTypeFilter = "all" | AlertType;

function AlertTypeButton({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-xs rounded-md px-2.5 py-1 transition-colors ${
        active
          ? "bg-slate-800 text-white"
          : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
      }`}
    >
      {label}
    </button>
  );
}

// ── Main Export ──

export function AlertsPage() {
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [severityFilter, setSeverityFilter] = useState<"all" | Severity>("all");
  const [typeFilter, setTypeFilter] = useState<AlertTypeFilter>("all");

  const activeAlerts = useMemo(
    () => mockAlerts.filter((a) => !dismissedIds.has(a._id)),
    [dismissedIds]
  );

  const filteredAlerts = useMemo(() => {
    return activeAlerts.filter((a) => {
      if (severityFilter !== "all" && a.severity !== severityFilter) return false;
      if (typeFilter !== "all" && a.alert_type !== typeFilter) return false;
      return true;
    });
  }, [activeAlerts, severityFilter, typeFilter]);

  const criticalCount = activeAlerts.filter((a) => a.severity === "critical").length;
  const warningCount = activeAlerts.filter((a) => a.severity === "warning").length;
  const infoCount = activeAlerts.filter((a) => a.severity === "info").length;

  const handleDismiss = (id: string) => {
    setDismissedIds((prev) => new Set(prev).add(id));
  };

  const handleMarkAllRead = () => {
    // In a real app this would update `notified` in the DB
  };

  const handleClearDismissed = () => {
    setDismissedIds(new Set());
  };

  const alertTypes: Array<{ value: AlertTypeFilter; label: string }> = [
    { value: "all", label: "All Types" },
    { value: "structure_changed", label: "Structure Changed" },
    { value: "zero_links", label: "Zero Links" },
    { value: "low_confidence", label: "Low Confidence" },
    { value: "link_count_drop", label: "Link Count Drop" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Alerts</h1>
        <p className="text-sm text-slate-500">
          Review system alerts for source changes, extraction failures, and confidence drops.
        </p>
      </div>

      {/* Stats bar */}
      <AlertStatsBar alerts={activeAlerts} />

      {/* Top bar: filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity toggles */}
          <FilterToggle
            label="All"
            count={activeAlerts.length}
            active={severityFilter === "all"}
            onClick={() => setSeverityFilter("all")}
          />
          <FilterToggle
            label="Critical"
            count={criticalCount}
            active={severityFilter === "critical"}
            onClick={() => setSeverityFilter("critical")}
            severity="critical"
          />
          <FilterToggle
            label="Warning"
            count={warningCount}
            active={severityFilter === "warning"}
            onClick={() => setSeverityFilter("warning")}
            severity="warning"
          />
          <FilterToggle
            label="Info"
            count={infoCount}
            active={severityFilter === "info"}
            onClick={() => setSeverityFilter("info")}
            severity="info"
          />
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs gap-1.5"
            onClick={handleMarkAllRead}
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark All Read
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs text-slate-500 gap-1.5"
            onClick={handleClearDismissed}
          >
            <Trash2 className="h-3.5 w-3.5" />
            Clear Dismissed
          </Button>
        </div>
      </div>

      {/* Alert type filter row */}
      <div className="flex flex-wrap gap-1.5">
        {alertTypes.map((at) => (
          <AlertTypeButton
            key={at.value}
            label={at.label}
            active={typeFilter === at.value}
            onClick={() => setTypeFilter(at.value)}
          />
        ))}
      </div>

      {/* Alert list */}
      {filteredAlerts.length === 0 ? (
        <EmptyAlerts />
      ) : (
        <div className="space-y-3">
          {filteredAlerts.map((alert) => (
            <AlertCard key={alert._id} alert={alert} onDismiss={handleDismiss} />
          ))}
        </div>
      )}
    </div>
  );
}
