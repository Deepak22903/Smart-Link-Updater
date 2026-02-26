"use client";

import { useState, useMemo } from "react";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Link2,
  FileText,
  Activity,
} from "lucide-react";
import {
  AreaChart,
  Area,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { theme, getHealthStyle, getExtractorStyle } from "@/lib/theme";
import {
  mockAnalytics,
  mockTimelineData,
  mockHourlyData,
  mockLinksTrendData,
  mockPostPerformance,
  mockSourcePerformance,
  mockExtractorPerformance,
  mockSitePerformance,
  mockSites,
} from "@/lib/mock-data";

// ── Helpers ──

const periodOptions = [
  { value: 7, label: "7d" },
  { value: 30, label: "30d" },
  { value: 60, label: "60d" },
  { value: 90, label: "90d" },
];

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatHour(hour: number): string {
  if (hour === 0) return "12am";
  if (hour === 12) return "12pm";
  return hour < 12 ? `${hour}am` : `${hour - 12}pm`;
}

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return "—";
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

function truncateUrl(url: string, max = 40): string {
  const clean = url.replace(/^https?:\/\//, "");
  return clean.length > max ? clean.slice(0, max) + "…" : clean;
}

// ── Custom Tooltip ──

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-white px-3 py-2 shadow-lg text-xs">
      <p className="font-medium text-slate-700 mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <div key={i} className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-slate-500">{entry.name}:</span>
          <span className="font-semibold">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

// ── Summary Card ──

function SummaryCard({
  label,
  value,
  change,
  subtitle,
  icon: Icon,
  accentColor,
}: {
  label: string;
  value: string;
  change?: number;
  subtitle?: string;
  icon: React.ElementType;
  accentColor: string;
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className="absolute top-0 left-0 h-1 w-full" style={{ backgroundColor: accentColor }} />
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
            {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          </div>
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg"
            style={{ backgroundColor: `${accentColor}18` }}
          >
            <Icon className="h-5 w-5" style={{ color: accentColor }} />
          </div>
        </div>
        {change !== undefined && (
          <div className="mt-2 flex items-center gap-1 text-xs">
            {change >= 0 ? (
              <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-red-500" />
            )}
            <span className={change >= 0 ? "text-emerald-600 font-medium" : "text-red-600 font-medium"}>
              {change >= 0 ? "↑" : "↓"} {Math.abs(change)}%
            </span>
            <span className="text-slate-400">vs previous period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Component ──

export function AnalyticsPage() {
  const [period, setPeriod] = useState(30);
  const siteKeys = Object.keys(mockSites);

  // Slice timeline data to match selected period
  const timeline = useMemo(() => mockTimelineData.slice(-period), [period]);
  const linksTrend = useMemo(() => mockLinksTrendData.slice(-period), [period]);

  // Flatten links trend for stacked bars
  const stackedLinksData = useMemo(
    () =>
      linksTrend.map((d) => ({
        date: formatDate(d.date),
        ...d.by_site,
      })),
    [linksTrend]
  );

  const formattedTimeline = useMemo(
    () => timeline.map((d) => ({ ...d, date: formatDate(d.date) })),
    [timeline]
  );

  return (
    <div className="space-y-6">
      {/* Header + Period Selector */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Analytics</h1>
          <p className="mt-1 text-sm text-slate-500">
            Performance metrics and trends across all posts and sites.
          </p>
        </div>
        <div className="flex rounded-lg border bg-white p-1 shadow-sm">
          {periodOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${
                period === opt.value
                  ? `bg-gradient-to-r ${theme.brand.gradient} text-white shadow-sm`
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Summary Cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Total Updates"
          value={mockAnalytics.total_updates.toString()}
          change={8}
          icon={Activity}
          accentColor={theme.brand.primary}
        />
        <SummaryCard
          label="Success Rate"
          value={`${mockAnalytics.success_rate}%`}
          change={2.1}
          icon={BarChart3}
          accentColor={theme.charts.success}
        />
        <SummaryCard
          label="Links Added"
          value={mockAnalytics.total_links_added.toString()}
          change={-3}
          subtitle={`avg ${mockAnalytics.avg_links_per_update}/update`}
          icon={Link2}
          accentColor={theme.charts.links}
        />
        <SummaryCard
          label="Active Posts"
          value={mockAnalytics.active_posts.toString()}
          icon={FileText}
          accentColor={theme.charts.noChanges}
        />
      </div>

      {/* ── Charts Grid ── */}
      <div className="grid gap-5 lg:grid-cols-2">
        {/* Chart 1: Update Timeline */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Update Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={formattedTimeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Area
                    type="monotone"
                    dataKey="successful"
                    name="Successful"
                    stackId="1"
                    fill={theme.charts.success}
                    fillOpacity={0.4}
                    stroke={theme.charts.success}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="failed"
                    name="Failed"
                    stackId="1"
                    fill={theme.charts.failed}
                    fillOpacity={0.4}
                    stroke={theme.charts.failed}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 2: Success Rate Trend */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Success Rate Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={formattedTimeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" interval="preserveStartEnd" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} stroke="#94a3b8" unit="%" />
                  <Tooltip content={<CustomTooltip />} />
                  <ReferenceLine y={90} stroke="#94a3b8" strokeDasharray="6 4" label={{ value: "90%", position: "insideTopRight", fontSize: 10, fill: "#94a3b8" }} />
                  <Line
                    type="monotone"
                    dataKey="success_rate"
                    name="Success Rate"
                    stroke={theme.brand.primary}
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 4, fill: theme.brand.primary }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 3: Links Added by Site */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Links Added by Site</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stackedLinksData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {siteKeys.map((key, idx) => (
                    <Bar
                      key={key}
                      dataKey={key}
                      name={mockSites[key]?.display_name ?? key}
                      stackId="sites"
                      fill={theme.charts.sites[idx % theme.charts.sites.length]}
                      radius={idx === siteKeys.length - 1 ? [3, 3, 0, 0] : [0, 0, 0, 0]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Chart 4: Hourly Activity */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Hourly Activity Pattern</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockHourlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="hour"
                    tick={{ fontSize: 11 }}
                    stroke="#94a3b8"
                    tickFormatter={formatHour}
                    interval={2}
                  />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip
                    content={<CustomTooltip />}
                    labelFormatter={(v) => formatHour(Number(v))}
                  />
                  <Bar
                    dataKey="total_updates"
                    name="Updates"
                    fill={theme.brand.primary}
                    radius={[3, 3, 0, 0]}
                    fillOpacity={0.8}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Performance Tables ── */}
      <Card>
        <CardContent className="p-0">
          <Tabs defaultValue="posts">
            <div className="border-b px-5 pt-4">
              <TabsList className="bg-transparent p-0 h-auto gap-4">
                <TabsTrigger
                  value="posts"
                  className="rounded-none border-b-2 border-transparent px-1 pb-3 pt-2 data-[state=active]:border-[#667eea] data-[state=active]:shadow-none"
                >
                  Posts
                </TabsTrigger>
                <TabsTrigger
                  value="sources"
                  className="rounded-none border-b-2 border-transparent px-1 pb-3 pt-2 data-[state=active]:border-[#667eea] data-[state=active]:shadow-none"
                >
                  Sources
                </TabsTrigger>
                <TabsTrigger
                  value="extractors"
                  className="rounded-none border-b-2 border-transparent px-1 pb-3 pt-2 data-[state=active]:border-[#667eea] data-[state=active]:shadow-none"
                >
                  Extractors
                </TabsTrigger>
                <TabsTrigger
                  value="sites"
                  className="rounded-none border-b-2 border-transparent px-1 pb-3 pt-2 data-[state=active]:border-[#667eea] data-[state=active]:shadow-none"
                >
                  Sites
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Posts Tab */}
            <TabsContent value="posts" className="m-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Post</TableHead>
                    <TableHead className="text-right">Updates</TableHead>
                    <TableHead>Success Rate</TableHead>
                    <TableHead className="text-right">Links Added</TableHead>
                    <TableHead className="text-right">Avg Links/Update</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockPostPerformance.map((p) => (
                    <TableRow key={p.post_id}>
                      <TableCell className="font-medium">{p.content_slug}</TableCell>
                      <TableCell className="text-right">{p.total_updates}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={p.success_rate} className="h-2 w-20" />
                          <span className="text-xs text-slate-600">{p.success_rate}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{p.total_links_added}</TableCell>
                      <TableCell className="text-right">{p.avg_links_per_update}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>

            {/* Sources Tab */}
            <TabsContent value="sources" className="m-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Source URL</TableHead>
                    <TableHead className="text-right">Extractions</TableHead>
                    <TableHead>Success Rate</TableHead>
                    <TableHead>Health</TableHead>
                    <TableHead className="text-right">Failures</TableHead>
                    <TableHead>Last Success</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockSourcePerformance.map((s, i) => {
                    const healthStyle = getHealthStyle(s.health);
                    return (
                      <TableRow key={i}>
                        <TableCell className="max-w-[240px]">
                          <span className="font-mono text-xs" title={s.source_url}>
                            {truncateUrl(s.source_url)}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">{s.total_extractions}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={s.success_rate} className="h-2 w-20" />
                            <span className="text-xs text-slate-600">{s.success_rate}%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className={`${healthStyle.bg} ${healthStyle.text} text-xs`}>
                            {s.health}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {s.consecutive_failures > 0 ? (
                            <span className="text-red-600 font-medium">{s.consecutive_failures}</span>
                          ) : (
                            <span className="text-slate-400">0</span>
                          )}
                        </TableCell>
                        <TableCell className="text-xs text-slate-500">{relativeTime(s.last_success)}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TabsContent>

            {/* Extractors Tab */}
            <TabsContent value="extractors" className="m-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Extractor</TableHead>
                    <TableHead className="text-right">Posts Using</TableHead>
                    <TableHead className="text-right">Total Links</TableHead>
                    <TableHead className="text-right">Avg Links/Post</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockExtractorPerformance.map((e) => {
                    const style = getExtractorStyle(e.extractor);
                    return (
                      <TableRow key={e.extractor}>
                        <TableCell>
                          <Badge variant="secondary" className={`${style.bg} ${style.text} text-xs`}>
                            {e.extractor}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">{e.posts_using}</TableCell>
                        <TableCell className="text-right">{e.total_links}</TableCell>
                        <TableCell className="text-right">{e.avg_links_per_post}</TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TabsContent>

            {/* Sites Tab */}
            <TabsContent value="sites" className="m-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Site</TableHead>
                    <TableHead>Display Name</TableHead>
                    <TableHead className="text-right">Links Added</TableHead>
                    <TableHead className="text-right">Posts Updated</TableHead>
                    <TableHead className="text-right">Avg Links/Post</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockSitePerformance.map((s) => (
                    <TableRow key={s.site_key}>
                      <TableCell className="font-medium font-mono text-sm">{s.site_key}</TableCell>
                      <TableCell>{s.display_name}</TableCell>
                      <TableCell className="text-right font-semibold">{s.links_added}</TableCell>
                      <TableCell className="text-right">{s.posts_updated}</TableCell>
                      <TableCell className="text-right">{s.avg_links_per_post}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
