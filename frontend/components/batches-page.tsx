"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import {
  Play,
  Square,
  Clock,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Minus,
  ExternalLink,
  Loader2,
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { theme, getStatusStyle } from "@/lib/theme";
import { mockBatchHistory, mockActiveBatch, mockPosts } from "@/lib/mock-data";
import type { BatchHistoryItem, PipelinePhase } from "@/lib/types";

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

function formatDuration(start: string, end: string | null): string {
  if (!end) return "\u2014";
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}m ${sec.toString().padStart(2, "0")}s`;
}

function formatElapsed(seconds: number): string {
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  return `${min}m ${sec.toString().padStart(2, "0")}s`;
}

function getPhaseLabel(phase: PipelinePhase): string {
  const labels: Record<PipelinePhase, string> = {
    queued: "Queued",
    scraping: "Scraping",
    extracting: "Extracting",
    deduplicating: "Deduplicating",
    updating_wp: "Updating WP",
    done: "Done",
    failed: "Failed",
  };
  return labels[phase];
}

function getPhaseBg(phase: PipelinePhase): string {
  switch (phase) {
    case "done":
      return theme.status.success.bg;
    case "failed":
      return theme.status.failed.bg;
    case "scraping":
    case "extracting":
    case "deduplicating":
    case "updating_wp":
      return theme.status.running.bg;
    case "queued":
      return theme.status.queued.bg;
    default:
      return theme.status.idle.bg;
  }
}

function getPhaseText(phase: PipelinePhase): string {
  switch (phase) {
    case "done":
      return theme.status.success.text;
    case "failed":
      return theme.status.failed.text;
    case "scraping":
    case "extracting":
    case "deduplicating":
    case "updating_wp":
      return theme.status.running.text;
    case "queued":
      return theme.status.queued.text;
    default:
      return theme.status.idle.text;
  }
}

function getPhaseBarColor(phase: PipelinePhase): string {
  switch (phase) {
    case "done":
      return theme.status.success.hex;
    case "failed":
      return theme.status.failed.hex;
    case "scraping":
    case "extracting":
    case "deduplicating":
    case "updating_wp":
      return theme.status.running.hex;
    default:
      return theme.status.queued.hex;
  }
}

function getInitiatorBadge(initiator: string) {
  switch (initiator) {
    case "cron":
      return (
        <Badge variant="secondary" className="text-xs font-normal">
          cron
        </Badge>
      );
    case "manual":
      return (
        <Badge
          className="text-xs font-normal text-white border-0"
          style={{ background: theme.brand.gradientCss }}
        >
          manual
        </Badge>
      );
    case "api":
      return (
        <Badge className={`text-xs font-normal ${theme.status.info.bg} ${theme.status.info.text} border-0`}>
          api
        </Badge>
      );
    default:
      return (
        <Badge variant="secondary" className="text-xs font-normal">
          {initiator}
        </Badge>
      );
  }
}

// ── Active Batch Section ──

function ActiveBatchSection() {
  const batch = mockActiveBatch;
  const overallProgress = (batch.completed_posts / batch.total_posts) * 100;

  return (
    <Card className="border-0 shadow-sm overflow-hidden">
      <CardContent className="p-5 space-y-4">
        {/* Progress bar header */}
        <div className="flex items-center gap-4">
          <div className="flex-1 space-y-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Loader2 className={`h-4 w-4 animate-spin ${theme.status.running.text}`} />
                <span className="text-sm font-medium text-slate-700">
                  Processing... {batch.completed_posts}/{batch.total_posts} posts
                  complete
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatElapsed(batch.elapsed_seconds)}
                </span>
              </div>
            </div>
            <div className="relative h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
              <div
                className={`absolute inset-y-0 left-0 rounded-full bg-gradient-to-r ${theme.brand.gradient} transition-all duration-500`}
                style={{ width: `${overallProgress}%` }}
              />
              {/* shimmer */}
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
          </div>
          <Button variant="outline" size="sm" className="shrink-0 gap-1.5">
            <Square className="h-3 w-3" />
            Stop Watching
          </Button>
        </div>

        {/* Pipeline cards - horizontal scroll */}
        <div className="flex gap-2.5 overflow-x-auto pb-1 -mx-1 px-1">
          {batch.posts.map((post) => (
            <div
              key={post.post_id}
              className={`shrink-0 w-[180px] rounded-lg border p-3 space-y-2 ${getPhaseBg(post.phase)}`}
            >
              <p className="text-xs font-medium text-slate-800 truncate">
                {post.content_slug}
              </p>
              <div className="flex items-center gap-1.5">
                {post.phase === "done" && (
                  <CheckCircle2 className={`h-3 w-3 ${theme.status.success.text}`} />
                )}
                {post.phase === "failed" && (
                  <XCircle className={`h-3 w-3 ${theme.status.failed.text}`} />
                )}
                {post.phase !== "done" && post.phase !== "failed" && post.phase !== "queued" && (
                  <Loader2 className={`h-3 w-3 animate-spin ${theme.status.running.text}`} />
                )}
                <span className={`text-xs font-medium ${getPhaseText(post.phase)}`}>
                  {getPhaseLabel(post.phase)}
                </span>
              </div>
              <div className="h-1 w-full rounded-full bg-white/60 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{
                    width: `${post.progress}%`,
                    backgroundColor: getPhaseBarColor(post.phase),
                  }}
                />
              </div>
              {post.error && (
                <p className={`text-[10px] leading-tight ${theme.status.failed.text}`}>
                  {post.error}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Batch Detail (expandable panel) ──

function BatchDetail({ batch }: { batch: BatchHistoryItem }) {
  const [openPosts, setOpenPosts] = useState<Set<number>>(new Set());

  // Generate mock per-post results from the batch
  const postResults = useMemo(() => {
    const statuses: Array<"success" | "failed" | "no_changes"> = [];
    for (let i = 0; i < batch.successful_posts; i++) statuses.push("success");
    for (let i = 0; i < batch.failed_posts; i++) statuses.push("failed");
    for (let i = 0; i < batch.no_changes_posts; i++) statuses.push("no_changes");
    // pad with success if needed
    while (statuses.length < batch.total_posts) statuses.push("success");

    return statuses.map((status, idx) => {
      const post = mockPosts[idx % mockPosts.length];
      return {
        post_id: post.post_id,
        content_slug: post.content_slug,
        status,
        links_found: status === "failed" ? 0 : Math.floor(Math.random() * 10) + 2,
        links_added: status === "failed" ? 0 : status === "no_changes" ? 0 : Math.floor(Math.random() * 6) + 1,
        message:
          status === "success"
            ? "Links extracted and updated successfully."
            : status === "no_changes"
            ? "No new or changed links detected."
            : "Extractor timed out — source page unreachable.",
        error: status === "failed" ? "Connection timeout after 30s" : null,
      };
    });
  }, [batch]);

  const toggle = (id: number) => {
    setOpenPosts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const statusStyle = getStatusStyle(batch.overall_status);

  return (
    <div className="px-4 pb-4 space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border bg-white p-3 text-center">
          <p className="text-xs text-slate-500">Total Posts</p>
          <p className="text-lg font-bold text-slate-800">{batch.total_posts}</p>
        </div>
        <div className={`rounded-lg border p-3 text-center ${theme.status.success.bg}`}>
          <p className={`text-xs ${theme.status.success.text}`}>Succeeded</p>
          <p className={`text-lg font-bold ${theme.status.success.text}`}>
            {batch.successful_posts}
          </p>
        </div>
        <div className={`rounded-lg border p-3 text-center ${theme.status.failed.bg}`}>
          <p className={`text-xs ${theme.status.failed.text}`}>Failed</p>
          <p className={`text-lg font-bold ${theme.status.failed.text}`}>
            {batch.failed_posts}
          </p>
        </div>
        <div className={`rounded-lg border p-3 text-center ${theme.status.noChanges.bg}`}>
          <p className={`text-xs ${theme.status.noChanges.text}`}>No Changes</p>
          <p className={`text-lg font-bold ${theme.status.noChanges.text}`}>
            {batch.no_changes_posts}
          </p>
        </div>
      </div>

      {/* Per-post accordion */}
      <div className="space-y-1">
        {postResults.map((pr) => {
          const prStyle = getStatusStyle(pr.status);
          return (
            <Collapsible
              key={`${batch.request_id}-${pr.post_id}`}
              open={openPosts.has(pr.post_id)}
              onOpenChange={() => toggle(pr.post_id)}
            >
              <CollapsibleTrigger asChild>
                <button className="flex w-full items-center gap-3 rounded-md border bg-white p-3 text-left hover:bg-slate-50 transition-colors">
                  {openPosts.has(pr.post_id) ? (
                    <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />
                  )}
                  <span className="text-sm font-medium text-slate-700 flex-1 truncate">
                    {pr.content_slug}
                  </span>
                  <Badge
                    className={`text-xs font-normal border-0 ${prStyle.bg} ${prStyle.text}`}
                  >
                    {pr.status === "no_changes" ? "no changes" : pr.status}
                  </Badge>
                  <span className="text-xs text-slate-500 whitespace-nowrap">
                    {pr.links_found} found / {pr.links_added} added
                  </span>
                </button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="ml-7 border-l-2 border-slate-200 pl-4 py-2 space-y-1.5">
                  <p className="text-xs text-slate-600">{pr.message}</p>
                  {pr.error && (
                    <p className={`text-xs ${theme.status.failed.text}`}>{pr.error}</p>
                  )}
                  <Link
                    href={`/posts/${pr.post_id}`}
                    className="inline-flex items-center gap-1 text-xs font-medium hover:underline"
                    style={{ color: theme.brand.primary }}
                  >
                    View Logs
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </div>
              </CollapsibleContent>
            </Collapsible>
          );
        })}
      </div>
    </div>
  );
}

// ── Batch History Table ──

function BatchHistoryTable() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <Card className="border-0 shadow-sm overflow-hidden">
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50/50">
              <TableHead className="w-8" />
              <TableHead className="text-xs font-medium text-slate-500">Request ID</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Started</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Duration</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Initiator</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Status</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Posts</TableHead>
              <TableHead className="text-xs font-medium text-slate-500">Results</TableHead>
              <TableHead className="text-xs font-medium text-slate-500 text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockBatchHistory.map((batch) => {
              const isExpanded = expandedId === batch.request_id;
              const statusStyle = getStatusStyle(batch.overall_status);

              return (
                <Collapsible
                  key={batch.request_id}
                  open={isExpanded}
                  onOpenChange={() =>
                    setExpandedId(isExpanded ? null : batch.request_id)
                  }
                  asChild
                >
                  <>
                    <TableRow
                      className={`cursor-pointer transition-colors ${
                        isExpanded ? "bg-slate-50" : "hover:bg-slate-50/50"
                      }`}
                    >
                      <TableCell className="w-8">
                        <CollapsibleTrigger asChild>
                          <button className="p-1 rounded hover:bg-slate-200/50">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 text-slate-400" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-slate-400" />
                            )}
                          </button>
                        </CollapsibleTrigger>
                      </TableCell>
                      <TableCell>
                        <code className="text-xs font-mono text-slate-600">
                          {batch.request_id.slice(0, 8)}
                        </code>
                      </TableCell>
                      <TableCell>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <span className="text-xs text-slate-600 cursor-default">
                              {relativeTime(batch.created_at)}
                            </span>
                          </TooltipTrigger>
                          <TooltipContent>
                            {new Date(batch.created_at).toLocaleString("en-US", {
                              timeZone: "UTC",
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                              hour12: false,
                            })}
                            {" UTC"}
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-slate-600">
                          {formatDuration(batch.created_at, batch.completed_at)}
                        </span>
                      </TableCell>
                      <TableCell>{getInitiatorBadge(batch.initiator)}</TableCell>
                      <TableCell>
                        <Badge
                          className={`text-xs font-normal border-0 ${statusStyle.bg} ${statusStyle.text}`}
                        >
                          {batch.overall_status === "no_changes"
                            ? "no changes"
                            : batch.overall_status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs text-slate-600">
                          {batch.total_posts} total
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-xs inline-flex items-center gap-1.5">
                          <span style={{ color: theme.status.success.hex }}>
                            {batch.successful_posts} &#10003;
                          </span>
                          <span className="text-slate-300">&middot;</span>
                          <span style={{ color: theme.status.failed.hex }}>
                            {batch.failed_posts} &#10007;
                          </span>
                          <span className="text-slate-300">&middot;</span>
                          <span style={{ color: theme.status.noChanges.hex }}>
                            {batch.no_changes_posts} &#9670;
                          </span>
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <CollapsibleTrigger asChild>
                          <Button variant="ghost" size="sm" className="text-xs h-7">
                            {isExpanded ? "Hide" : "View Details"}
                          </Button>
                        </CollapsibleTrigger>
                      </TableCell>
                    </TableRow>
                    <CollapsibleContent asChild>
                      <tr>
                        <td colSpan={9} className="p-0">
                          <BatchDetail batch={batch} />
                        </td>
                      </tr>
                    </CollapsibleContent>
                  </>
                </Collapsible>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// ── Skeleton ──

function BatchesSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-40 w-full rounded-xl" />
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full rounded-lg" />
        ))}
      </div>
    </div>
  );
}

// ── Main Export ──

export function BatchesPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold text-slate-900">Batches</h1>
        <p className="text-sm text-slate-500">
          Monitor active batch runs and browse execution history.
        </p>
      </div>

      {/* Active batch (conditional) */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Play className="h-4 w-4" style={{ color: theme.brand.primary }} />
          Active Batch
        </h2>
        <ActiveBatchSection />
      </div>

      {/* Batch History */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <Clock className="h-4 w-4 text-slate-400" />
          Batch History
        </h2>
        <BatchHistoryTable />
      </div>
    </div>
  );
}
