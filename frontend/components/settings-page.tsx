"use client";

import { useState } from "react";
import {
  Clock,
  Globe,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  AlertTriangle,
  Loader2,
  Trash2,
  RotateCcw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { theme } from "@/lib/theme";
import { mockCronSettings } from "@/lib/mock-data";

const scheduleOptions = [
  { value: "every_5_minutes", label: "Every 5 minutes" },
  { value: "every_15_minutes", label: "Every 15 minutes" },
  { value: "every_30_minutes", label: "Every 30 minutes" },
  { value: "hourly", label: "Hourly" },
  { value: "twicedaily", label: "Twice Daily" },
  { value: "daily", label: "Daily" },
];

function getScheduleLabel(value: string) {
  return scheduleOptions.find((o) => o.value === value)?.label ?? value;
}

// Compute mock next-run ticks for the visual timeline
function getScheduleTicks(schedule: string): number[] {
  const intervalsPerDay: Record<string, number> = {
    every_5_minutes: 288,
    every_15_minutes: 96,
    every_30_minutes: 48,
    hourly: 24,
    twicedaily: 2,
    daily: 1,
  };
  const count = Math.min(intervalsPerDay[schedule] ?? 24, 48); // cap visually
  const step = 24 / count;
  const ticks: number[] = [];
  for (let i = 0; i < count; i++) {
    ticks.push(i * step);
  }
  return ticks;
}

export function SettingsPage() {
  const [cronEnabled, setCronEnabled] = useState(mockCronSettings.enabled);
  const [schedule, setSchedule] = useState(mockCronSettings.schedule);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<"success" | "error" | null>(null);
  const [copied, setCopied] = useState(false);
  const [saved, setSaved] = useState(false);

  const apiUrl = "https://smartlink-api-601738079869.us-central1.run.app";
  const scheduleTicks = getScheduleTicks(schedule);

  function handleTestConnection() {
    setIsTesting(true);
    setTestResult(null);
    setTimeout(() => {
      setIsTesting(false);
      setTestResult("success");
    }, 1500);
  }

  function handleCopyUrl() {
    navigator.clipboard.writeText(apiUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">
          Configure scheduled updates, API connection, and system preferences.
        </p>
      </div>

      {/* ── Section 1: Cron Schedule ── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ background: theme.brand.gradientCss }}
            >
              <Clock className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle>Scheduled Updates</CardTitle>
              <CardDescription>
                Automatically run batch updates on a recurring schedule.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Enable toggle */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label className="text-base font-medium">Enable automatic updates</Label>
              <p className="text-sm text-slate-500">
                When enabled, posts will be updated on the selected schedule.
              </p>
            </div>
            <Switch checked={cronEnabled} onCheckedChange={setCronEnabled} />
          </div>

          {/* Schedule selector */}
          <div className="space-y-2">
            <Label>Schedule</Label>
            <Select value={schedule} onValueChange={setSchedule} disabled={!cronEnabled}>
              <SelectTrigger className="w-full max-w-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {scheduleOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Status info rows */}
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-3 rounded-lg border p-3">
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
              <div>
                <p className="text-xs font-medium text-slate-500">Last run</p>
                <p className="text-sm font-semibold text-slate-900">
                  Feb 26, 2026 at 10:00 AM IST
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg border p-3">
              <Clock className="h-5 w-5 shrink-0 text-blue-500" />
              <div>
                <p className="text-xs font-medium text-slate-500">Next run</p>
                <p className="text-sm font-semibold text-slate-900">
                  {cronEnabled
                    ? "Feb 26, 2026 at 11:00 AM IST"
                    : "—  Disabled"}
                </p>
              </div>
            </div>
          </div>

          {/* Visual timeline */}
          {cronEnabled && (
            <div className="space-y-2">
              <Label className="text-xs text-slate-500">Daily schedule preview (24h)</Label>
              <div className="relative h-8 rounded-full bg-slate-100">
                {/* Hour marks */}
                {[0, 6, 12, 18].map((h) => (
                  <div
                    key={h}
                    className="absolute top-full mt-1 text-[10px] text-slate-400"
                    style={{ left: `${(h / 24) * 100}%`, transform: "translateX(-50%)" }}
                  >
                    {h === 0 ? "12am" : h === 6 ? "6am" : h === 12 ? "12pm" : "6pm"}
                  </div>
                ))}
                {/* Schedule ticks */}
                {scheduleTicks.map((h, i) => (
                  <div
                    key={i}
                    className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full"
                    style={{
                      left: `${(h / 24) * 100}%`,
                      background: theme.brand.gradientCss,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          <Button
            onClick={handleSave}
            className={`bg-gradient-to-r ${theme.brand.gradient} text-white`}
          >
            {saved ? (
              <>
                <Check className="mr-2 h-4 w-4" />
                Saved
              </>
            ) : (
              "Save Schedule"
            )}
          </Button>
        </CardContent>
      </Card>

      {/* ── Section 2: API Configuration ── */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div
              className="flex h-10 w-10 items-center justify-center rounded-lg"
              style={{ background: theme.brand.gradientCss }}
            >
              <Globe className="h-5 w-5 text-white" />
            </div>
            <div>
              <CardTitle>API Connection</CardTitle>
              <CardDescription>
                SmartLink backend API configuration and health.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* API URL */}
          <div className="space-y-2">
            <Label>API Base URL</Label>
            <div className="flex gap-2">
              <Input value={apiUrl} readOnly className="font-mono text-sm bg-slate-50" />
              <Button variant="outline" size="icon" onClick={handleCopyUrl}>
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          {/* Connection status */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="flex items-center gap-3">
              <div className={`h-3 w-3 rounded-full ${testResult === "error" ? theme.health.failing.dot : theme.health.healthy.dot}`} />
              <div>
                <p className="text-sm font-medium">
                  {testResult === "error" ? "Disconnected" : "Connected"}
                </p>
                <p className="text-xs text-slate-500">
                  {testResult === "error"
                    ? "Unable to reach the API server"
                    : "API is reachable and responding"}
                </p>
              </div>
            </div>
            <Button variant="outline" onClick={handleTestConnection} disabled={isTesting}>
              {isTesting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Testing…
                </>
              ) : (
                "Test Connection"
              )}
            </Button>
          </div>

          {/* Health details */}
          {testResult === "success" && (
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border p-3">
                <p className="text-xs font-medium text-slate-500">API Version</p>
                <p className="text-sm font-semibold">v2.1.0</p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-xs font-medium text-slate-500">Uptime</p>
                <p className="text-sm font-semibold">14d 6h 32m</p>
              </div>
              <div className="rounded-lg border p-3">
                <p className="text-xs font-medium text-slate-500">MongoDB</p>
                <div className="flex items-center gap-1.5">
                  <div className={`h-2 w-2 rounded-full ${theme.health.healthy.dot}`} />
                  <p className="text-sm font-semibold">Connected</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Section 3: Danger Zone ── */}
      <Card className="border-red-200">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-100">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-red-700">Danger Zone</CardTitle>
              <CardDescription>
                Irreversible actions that affect stored data. Proceed with caution.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Clear Fingerprints */}
          <div className="flex items-center justify-between rounded-lg border border-red-200 p-4">
            <div>
              <p className="text-sm font-medium text-slate-900">Clear All Fingerprints</p>
              <p className="text-xs text-slate-500">
                Removes all link deduplication fingerprints. Links may be re-added to posts.
              </p>
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm" className="border-red-300 text-red-600 hover:bg-red-50">
                  <Trash2 className="mr-2 h-3.5 w-3.5" />
                  Clear
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Clear all fingerprints?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete all link fingerprints from the database.
                    Previously added links may be re-inserted on the next extraction.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction className="bg-red-600 hover:bg-red-700">
                    Clear Fingerprints
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>

          {/* Reset Cron History */}
          <div className="flex items-center justify-between rounded-lg border border-red-200 p-4">
            <div>
              <p className="text-sm font-medium text-slate-900">Reset Cron History</p>
              <p className="text-xs text-slate-500">
                Deletes all scheduled run history. Does not affect cron settings or schedule.
              </p>
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm" className="border-red-300 text-red-600 hover:bg-red-50">
                  <RotateCcw className="mr-2 h-3.5 w-3.5" />
                  Reset
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Reset cron history?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete all scheduled update history records.
                    Your cron settings and schedule will remain unchanged.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction className="bg-red-600 hover:bg-red-700">
                    Reset History
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
