"use client";

import { useState, useMemo, useEffect, useId } from "react";
import Link from "next/link";
import {
  Search,
  LayoutGrid,
  List,
  Plus,
  Link as LinkIcon,
  Clock,
  Bell,
  MoreHorizontal,
  Settings2,
  Trash2,
  ArrowUpDown,
  X,
  Zap,
  FileX2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { theme, getHealthStyle, getExtractorStyle, getStatusStyle } from "@/lib/theme";
import { mockPosts, mockSites } from "@/lib/mock-data";
import type { PostListItem, ExtractionMode } from "@/lib/types";

import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

// ── Helpers ──────────────────────────────────────────────────────────

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function isStale(dateStr: string | null): boolean {
  if (!dateStr) return true;
  return Date.now() - new Date(dateStr).getTime() > 24 * 60 * 60 * 1000;
}

const SITE_COLORS = [
  "bg-indigo-100 text-indigo-700",
  "bg-amber-100 text-amber-700",
  "bg-emerald-100 text-emerald-700",
  "bg-pink-100 text-pink-700",
  "bg-cyan-100 text-cyan-700",
  "bg-violet-100 text-violet-700",
];

function getSiteColor(index: number) {
  return SITE_COLORS[index % SITE_COLORS.length];
}

const modeConfig: Record<ExtractionMode, { label: string; className: string }> = {
  links: { label: "Links", className: "bg-blue-100 text-blue-700 border-blue-200" },
  promo_codes: { label: "Promo Codes", className: "bg-orange-100 text-orange-700 border-orange-200" },
  both: { label: "Both", className: "bg-purple-100 text-purple-700 border-purple-200" },
};

const extractorNames = [...new Set(mockPosts.map((p) => p.extractor))];
const siteKeys = Object.keys(mockSites);

// Simulated links-today per post (random but deterministic)
const linksToday: Record<number, number> = {};
mockPosts.forEach((p) => {
  linksToday[p.post_id] = ((p.post_id * 7 + 3) % 12) + 1;
});

// ── Site Avatar ──────────────────────────────────────────────────────

function SiteAvatars({
  sitePostIds,
  max = 4,
}: {
  sitePostIds: Record<string, number>;
  max?: number;
}) {
  const sites = Object.keys(sitePostIds);
  const shown = sites.slice(0, max);
  const overflow = sites.length - max;

  return (
    <div className="flex items-center -space-x-1.5">
      {shown.map((siteKey, i) => {
        const site = mockSites[siteKey];
        const letter = site?.display_name?.charAt(0) ?? siteKey.charAt(0).toUpperCase();
        return (
          <div
            key={siteKey}
            className={cn(
              "flex h-6 w-6 items-center justify-center rounded-full border-2 border-white text-[10px] font-semibold",
              getSiteColor(i)
            )}
            title={site?.display_name ?? siteKey}
          >
            {letter}
          </div>
        );
      })}
      {overflow > 0 && (
        <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-200 text-[10px] font-semibold text-slate-600">
          +{overflow}
        </div>
      )}
    </div>
  );
}

// ── Post Actions Dropdown ────────────────────────────────────────────

function PostActionsDropdown() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-sm" className="h-7 w-7">
          <MoreHorizontal className="h-4 w-4" />
          <span className="sr-only">Post actions</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem>
          <Settings2 className="h-4 w-4" />
          Edit Config
        </DropdownMenuItem>
        <DropdownMenuItem>
          <LinkIcon className="h-4 w-4" />
          Add Manual Links
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive">
          <Trash2 className="h-4 w-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// ── Post Card ────────────────────────────────────────────────────────

function PostCard({ post }: { post: PostListItem }) {
  const healthStyle = getHealthStyle(post.health_status);
  const extractorStyle = getExtractorStyle(post.extractor);
  const mode = modeConfig[post.extraction_mode];

  return (
    <Card className="group relative gap-0 overflow-hidden py-0 transition-all duration-200 hover:shadow-md hover:scale-[1.01]">
      {/* Left border colored by health */}
      <div
        className={cn(
          "absolute inset-y-0 left-0 w-[3px]",
          post.health_status === "healthy" && "bg-emerald-500",
          post.health_status === "warning" && "bg-amber-500",
          post.health_status === "failing" && "bg-red-500",
          post.health_status === "unknown" && "bg-slate-400"
        )}
      />

      <CardHeader className="gap-2 px-5 pt-4 pb-0">
        {/* Title + health dot */}
        <div className="flex items-center justify-between gap-2">
          <h3 className="truncate text-sm font-semibold text-slate-900">
            {post.content_slug}
          </h3>
          <span
            className={cn("h-2.5 w-2.5 shrink-0 rounded-full", healthStyle.dot)}
            title={post.health_status}
          />
        </div>

        {/* Badge row */}
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge
            variant="secondary"
            className={cn("border text-[11px]", extractorStyle.bg, extractorStyle.text)}
          >
            {post.extractor}
          </Badge>
          <Badge
            variant="secondary"
            className={cn("border text-[11px]", mode.className)}
          >
            {mode.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="px-5 pt-3 pb-0">
        {/* Stats row */}
        <div className="flex flex-col gap-1.5 text-xs text-slate-500">
          <div className="flex items-center gap-1.5">
            <LinkIcon className="h-3.5 w-3.5" />
            <span className="font-medium text-slate-700">
              {linksToday[post.post_id]} links today
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            <span className={cn(isStale(post.last_updated) && "text-slate-400")}>
              Last updated: {relativeTime(post.last_updated)}
            </span>
            {post.send_notifications && (
              <Bell className="ml-auto h-3.5 w-3.5 text-slate-400" />
            )}
          </div>
        </div>

        {/* Sites row */}
        <div className="mt-3">
          <SiteAvatars sitePostIds={post.site_post_ids} />
        </div>
      </CardContent>

      <CardFooter className="flex items-center justify-between px-5 pt-3 pb-4">
        <Button
          variant="outline"
          size="sm"
          className="h-7 gap-1 border-[#667eea]/30 text-xs text-[#667eea] hover:bg-[#667eea]/5"
        >
          Update
        </Button>
        <div className="flex items-center gap-1">
          <Link
            href={`/posts/${post.post_id}`}
            className="text-xs font-medium text-[#667eea] hover:underline"
          >
            {"View \u2192"}
          </Link>
          <PostActionsDropdown />
        </div>
      </CardFooter>
    </Card>
  );
}

// ── Skeleton Card ────────────────────────────────────────────────────

function PostCardSkeleton() {
  return (
    <Card className="gap-0 py-0">
      <CardHeader className="gap-2 px-5 pt-4 pb-0">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-36" />
          <Skeleton className="h-2.5 w-2.5 rounded-full" />
        </div>
        <div className="flex gap-1.5">
          <Skeleton className="h-5 w-20 rounded-md" />
          <Skeleton className="h-5 w-14 rounded-md" />
        </div>
      </CardHeader>
      <CardContent className="px-5 pt-3 pb-0">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="mt-1.5 h-3 w-32" />
        <div className="mt-3 flex -space-x-1.5">
          <Skeleton className="h-6 w-6 rounded-full" />
          <Skeleton className="h-6 w-6 rounded-full" />
        </div>
      </CardContent>
      <CardFooter className="flex items-center justify-between px-5 pt-3 pb-4">
        <Skeleton className="h-7 w-16 rounded-md" />
        <Skeleton className="h-4 w-12" />
      </CardFooter>
    </Card>
  );
}

// ── Empty State ──────────────────────────────────────────────────────

function EmptyState({ onClear }: { onClear: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
        <FileX2 className="h-8 w-8 text-slate-400" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-slate-900">No posts found</h3>
      <p className="mt-1 text-sm text-slate-500">Try adjusting your filters</p>
      <Button variant="outline" className="mt-4" onClick={onClear}>
        Clear Filters
      </Button>
    </div>
  );
}

// ── Filter Pill ──────────────────────────────────────────────────────

function FilterPill({
  label,
  value,
  onRemove,
}: {
  label: string;
  value: string;
  onRemove: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-[#667eea]/10 px-2.5 py-1 text-xs font-medium text-[#667eea]">
      {label}: {value}
      <button
        onClick={onRemove}
        className="ml-0.5 rounded-full p-0.5 hover:bg-[#667eea]/20"
        aria-label={`Remove ${label} filter`}
      >
        <X className="h-3 w-3" />
      </button>
    </span>
  );
}

// ── Batch Controls Bar ───────────────────────────────────────────────

function BatchControlsBar({
  count,
  onDeselect,
  targetSite,
  onTargetSiteChange,
}: {
  count: number;
  onDeselect: () => void;
  targetSite: string;
  onTargetSiteChange: (v: string) => void;
}) {
  const batchId = useId();
  return (
    <div
      className={cn(
        "fixed inset-x-0 bottom-0 z-40 border-t bg-white/95 px-6 py-3 shadow-[0_-4px_12px_rgba(0,0,0,0.08)] backdrop-blur-sm",
        "animate-in slide-in-from-bottom-4 duration-300",
        "lg:left-[260px]"
      )}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="flex items-center gap-3 text-sm">
          <span className="font-medium text-slate-900">
            {count} post{count !== 1 ? "s" : ""} selected
          </span>
          <button
            onClick={onDeselect}
            className="text-xs text-[#667eea] hover:underline"
          >
            Deselect All
          </button>
        </div>

        <div className="flex items-center gap-3">
          <Select value={targetSite} onValueChange={onTargetSiteChange} name={`${batchId}-site`}>
            <SelectTrigger className="h-8 w-[160px] text-xs">
              <SelectValue placeholder="All Sites" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sites</SelectItem>
              {siteKeys.map((key) => (
                <SelectItem key={key} value={key}>
                  {mockSites[key].display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            size="sm"
            className="gap-1.5 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white hover:opacity-90"
          >
            <Zap className="h-3.5 w-3.5" />
            Update Selected
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Sort helpers ─────────────────────────────────────────────────────

type SortKey = "content_slug" | "last_updated" | "links_today";
type SortDir = "asc" | "desc";

function sortPosts(posts: PostListItem[], key: SortKey, dir: SortDir): PostListItem[] {
  return [...posts].sort((a, b) => {
    let cmp = 0;
    if (key === "content_slug") {
      cmp = a.content_slug.localeCompare(b.content_slug);
    } else if (key === "last_updated") {
      const aT = a.last_updated ? new Date(a.last_updated).getTime() : 0;
      const bT = b.last_updated ? new Date(b.last_updated).getTime() : 0;
      cmp = aT - bT;
    } else if (key === "links_today") {
      cmp = (linksToday[a.post_id] ?? 0) - (linksToday[b.post_id] ?? 0);
    }
    return dir === "asc" ? cmp : -cmp;
  });
}

// ── Sortable Header ─────────────────────────────────────────────────

function SortableHead({
  label,
  sortKey,
  currentKey,
  currentDir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentKey: SortKey;
  currentDir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const isActive = currentKey === sortKey;
  return (
    <TableHead>
      <button
        className="flex items-center gap-1 font-medium hover:text-slate-900"
        onClick={() => onSort(sortKey)}
      >
        {label}
        <ArrowUpDown
          className={cn(
            "h-3.5 w-3.5",
            isActive ? "text-[#667eea]" : "text-slate-400"
          )}
        />
        {isActive && (
          <span className="text-[10px] text-[#667eea]">
            {currentDir === "asc" ? "\u2191" : "\u2193"}
          </span>
        )}
      </button>
    </TableHead>
  );
}

// ── Main PostsList Component ─────────────────────────────────────────

export function PostsList() {
  const [view, setView] = useState<"grid" | "table">("grid");
  const [search, setSearch] = useState("");
  const [filterExtractor, setFilterExtractor] = useState("all");
  const [filterHealth, setFilterHealth] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [targetSite, setTargetSite] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("content_slug");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [loading, setLoading] = useState(true);

  // Simulate loading
  useEffect(() => {
    const id = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(id);
  }, []);

  // Filter logic
  const filtered = useMemo(() => {
    let result = mockPosts;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (p) =>
          p.content_slug.toLowerCase().includes(q) ||
          String(p.post_id).includes(q)
      );
    }
    if (filterExtractor !== "all") {
      result = result.filter((p) => p.extractor === filterExtractor);
    }
    if (filterHealth !== "all") {
      result = result.filter((p) => p.health_status === filterHealth);
    }
    if (filterStatus !== "all") {
      // Map filter to health for now since posts use health_status
      result = result.filter((p) => {
        if (filterStatus === "idle") return p.health_status === "unknown";
        if (filterStatus === "success") return p.health_status === "healthy";
        if (filterStatus === "failed") return p.health_status === "failing";
        if (filterStatus === "no_changes") return p.health_status === "warning";
        return true;
      });
    }
    return sortPosts(result, sortKey, sortDir);
  }, [search, filterExtractor, filterHealth, filterStatus, sortKey, sortDir]);

  const hasFilters =
    filterExtractor !== "all" || filterHealth !== "all" || filterStatus !== "all";

  function clearFilters() {
    setFilterExtractor("all");
    setFilterHealth("all");
    setFilterStatus("all");
    setSearch("");
  }

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  function toggleSelect(id: number) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filtered.map((p) => p.post_id)));
    }
  }

  // Stable IDs for Radix Select (prevents SSR hydration ID mismatch)
  const id = useId();

  // ── Render ──

  return (
    <div className="space-y-4">
      {/* ── Top Bar ── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search posts by name or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-9 w-full rounded-md border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-[#667eea] focus:ring-2 focus:ring-[#667eea]/20"
          />
        </div>

        {/* Filters + View Toggle + Add */}
        <div className="flex flex-wrap items-center gap-2">
          <Select value={filterExtractor} onValueChange={setFilterExtractor} name={`${id}-extractor`}>
            <SelectTrigger className="h-9 w-[140px] text-xs">
              <SelectValue placeholder="Extractor" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Extractors</SelectItem>
              {extractorNames.map((name) => (
                <SelectItem key={name} value={name}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filterHealth} onValueChange={setFilterHealth} name={`${id}-health`}>
            <SelectTrigger className="h-9 w-[120px] text-xs">
              <SelectValue placeholder="Health" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Health</SelectItem>
              <SelectItem value="healthy">Healthy</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="failing">Failing</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filterStatus} onValueChange={setFilterStatus} name={`${id}-status`}>
            <SelectTrigger className="h-9 w-[130px] text-xs">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="idle">Idle</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="no_changes">No Changes</SelectItem>
            </SelectContent>
          </Select>

          {/* View toggle */}
          <div className="flex items-center rounded-md border border-slate-200 p-0.5">
            <button
              onClick={() => setView("grid")}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded",
                view === "grid"
                  ? "bg-[#667eea] text-white"
                  : "text-slate-400 hover:text-slate-600"
              )}
              aria-label="Grid view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              onClick={() => setView("table")}
              className={cn(
                "flex h-7 w-7 items-center justify-center rounded",
                view === "table"
                  ? "bg-[#667eea] text-white"
                  : "text-slate-400 hover:text-slate-600"
              )}
              aria-label="Table view"
            >
              <List className="h-4 w-4" />
            </button>
          </div>

          <Button
            size="sm"
            className="gap-1.5 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white hover:opacity-90"
          >
            <Plus className="h-3.5 w-3.5" />
            Add New Post
          </Button>
        </div>
      </div>

      {/* ── Active Filter Pills ── */}
      {hasFilters && (
        <div className="flex flex-wrap items-center gap-2">
          {filterExtractor !== "all" && (
            <FilterPill
              label="Extractor"
              value={filterExtractor}
              onRemove={() => setFilterExtractor("all")}
            />
          )}
          {filterHealth !== "all" && (
            <FilterPill
              label="Health"
              value={filterHealth}
              onRemove={() => setFilterHealth("all")}
            />
          )}
          {filterStatus !== "all" && (
            <FilterPill
              label="Status"
              value={filterStatus}
              onRemove={() => setFilterStatus("all")}
            />
          )}
        </div>
      )}

      {/* ── Loading State ── */}
      {loading && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <PostCardSkeleton key={i} />
          ))}
        </div>
      )}

      {/* ��─ Empty State ── */}
      {!loading && filtered.length === 0 && (
        <EmptyState onClear={clearFilters} />
      )}

      {/* ── Grid View ── */}
      {!loading && filtered.length > 0 && view === "grid" && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((post) => (
            <PostCard key={post.post_id} post={post} />
          ))}
        </div>
      )}

      {/* ── Table View ── */}
      {!loading && filtered.length > 0 && view === "table" && (
        <>
          <Card className="gap-0 overflow-hidden py-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        selectedIds.size === filtered.length && filtered.length > 0
                      }
                      onCheckedChange={toggleSelectAll}
                      aria-label="Select all posts"
                    />
                  </TableHead>
                  <SortableHead
                    label="Content Slug"
                    sortKey="content_slug"
                    currentKey={sortKey}
                    currentDir={sortDir}
                    onSort={handleSort}
                  />
                  <TableHead>Extractor</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Health</TableHead>
                  <SortableHead
                    label="Last Updated"
                    sortKey="last_updated"
                    currentKey={sortKey}
                    currentDir={sortDir}
                    onSort={handleSort}
                  />
                  <SortableHead
                    label="Links Today"
                    sortKey="links_today"
                    currentKey={sortKey}
                    currentDir={sortDir}
                    onSort={handleSort}
                  />
                  <TableHead>Sites</TableHead>
                  <TableHead className="w-10">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((post) => {
                  const healthStyle = getHealthStyle(post.health_status);
                  const extractorStyle = getExtractorStyle(post.extractor);
                  const mode = modeConfig[post.extraction_mode];
                  const isSelected = selectedIds.has(post.post_id);

                  return (
                    <TableRow
                      key={post.post_id}
                      data-state={isSelected ? "selected" : undefined}
                    >
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelect(post.post_id)}
                          aria-label={`Select ${post.content_slug}`}
                        />
                      </TableCell>
                      <TableCell>
                        <Link
                          href={`/posts/${post.post_id}`}
                          className="font-semibold text-slate-900 hover:text-[#667eea] hover:underline"
                        >
                          {post.content_slug}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn(
                            "border text-[11px]",
                            extractorStyle.bg,
                            extractorStyle.text
                          )}
                        >
                          {post.extractor}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="secondary"
                          className={cn("border text-[11px]", mode.className)}
                        >
                          {mode.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <span
                            className={cn(
                              "h-2 w-2 rounded-full",
                              healthStyle.dot
                            )}
                          />
                          <span className={cn("text-xs", healthStyle.text)}>
                            {post.health_status}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span
                          className={cn(
                            "text-xs",
                            isStale(post.last_updated)
                              ? "text-slate-400"
                              : "text-slate-600"
                          )}
                        >
                          {relativeTime(post.last_updated)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm font-medium text-slate-700">
                          {linksToday[post.post_id]}
                        </span>
                      </TableCell>
                      <TableCell>
                        <SiteAvatars sitePostIds={post.site_post_ids} />
                      </TableCell>
                      <TableCell>
                        <PostActionsDropdown />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </Card>

          {/* Batch controls bar */}
          {selectedIds.size > 0 && (
            <BatchControlsBar
              count={selectedIds.size}
              onDeselect={() => setSelectedIds(new Set())}
              targetSite={targetSite}
              onTargetSiteChange={setTargetSite}
            />
          )}
        </>
      )}
    </div>
  );
}
