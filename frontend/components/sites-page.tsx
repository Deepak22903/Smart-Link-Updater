"use client";

import { useState } from "react";
import {
  Globe,
  ExternalLink,
  FileText,
  RefreshCw,
  Pencil,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  Check,
  X,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { theme } from "@/lib/theme";
import { mockSites, mockPosts } from "@/lib/mock-data";
import type { SiteConfig } from "@/lib/types";

const buttonStyleOptions = [
  { value: "default", label: "Default", color: "#667eea" },
  { value: "gradient-blue", label: "Gradient Blue", color: "#3b82f6" },
  { value: "gradient-green", label: "Gradient Green", color: "#10b981" },
  { value: "solid-orange", label: "Solid Orange", color: "#f59e0b" },
  { value: "solid-red", label: "Solid Red", color: "#ef4444" },
  { value: "gradient-purple", label: "Gradient Purple", color: "#8b5cf6" },
];

function getStyleColor(style: string) {
  return buttonStyleOptions.find((s) => s.value === style)?.color ?? "#667eea";
}

function countPostsForSite(siteKey: string): number {
  return mockPosts.filter((p) => siteKey in (p.site_post_ids || {})).length;
}

function countAutoUpdateForSite(siteKey: string): number {
  return mockPosts.filter((p) => p.auto_update_sites?.includes(siteKey)).length;
}

export function SitesPage() {
  const [sites, setSites] = useState<Record<string, SiteConfig>>({ ...mockSites });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);

  // Form state
  const [formKey, setFormKey] = useState("");
  const [formName, setFormName] = useState("");
  const [formUrl, setFormUrl] = useState("");
  const [formUsername, setFormUsername] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formStyle, setFormStyle] = useState("default");
  const [showPassword, setShowPassword] = useState(false);

  function resetForm() {
    setFormKey("");
    setFormName("");
    setFormUrl("");
    setFormUsername("");
    setFormPassword("");
    setFormStyle("default");
    setShowPassword(false);
    setEditingKey(null);
  }

  function openAdd() {
    resetForm();
    setDialogOpen(true);
  }

  function openEdit(key: string) {
    const site = sites[key];
    if (!site) return;
    setEditingKey(key);
    setFormKey(key);
    setFormName(site.display_name);
    setFormUrl(site.base_url);
    setFormUsername(site.username);
    setFormPassword(site.app_password ?? "");
    setFormStyle(site.button_style);
    setShowPassword(false);
    setDialogOpen(true);
  }

  function handleSave() {
    const key = editingKey ?? formKey;
    if (!key || !formUrl || !formUsername) return;
    setSites((prev) => ({
      ...prev,
      [key]: {
        base_url: formUrl,
        username: formUsername,
        display_name: formName || key,
        button_style: formStyle,
        app_password: formPassword,
      },
    }));
    setDialogOpen(false);
    resetForm();
  }

  function handleDelete() {
    if (!deleteTarget) return;
    setSites((prev) => {
      const next = { ...prev };
      delete next[deleteTarget];
      return next;
    });
    setDeleteTarget(null);
  }

  const siteEntries = Object.entries(sites);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Sites</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage your WordPress sites — {siteEntries.length} site{siteEntries.length !== 1 && "s"} configured.
          </p>
        </div>
        <Button
          onClick={openAdd}
          className={`bg-gradient-to-r ${theme.brand.gradient} text-white`}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Site
        </Button>
      </div>

      {/* Sites Grid */}
      {siteEntries.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Globe className="h-12 w-12 text-slate-300" />
            <p className="mt-4 text-lg font-semibold text-slate-700">No sites configured</p>
            <p className="mt-1 text-sm text-slate-500">Add a WordPress site to get started.</p>
            <Button onClick={openAdd} className="mt-4" variant="outline">
              <Plus className="mr-2 h-4 w-4" />
              Add Site
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-5 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {siteEntries.map(([key, site]) => (
            <Card key={key} className="relative overflow-hidden">
              {/* Top color stripe */}
              <div
                className="h-1.5"
                style={{
                  background: `linear-gradient(90deg, ${getStyleColor(site.button_style)}, ${getStyleColor(site.button_style)}88)`,
                }}
              />
              <CardContent className="p-5 space-y-4">
                {/* Title + URL */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{site.display_name}</h3>
                  <a
                    href={site.base_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-0.5 inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                  >
                    {site.base_url.replace(/^https?:\/\//, "")}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                {/* Meta rows */}
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Username</span>
                    <span className="font-medium text-slate-700">{site.username}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Button Style</span>
                    <Badge variant="secondary" className="gap-1.5">
                      <span
                        className="inline-block h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: getStyleColor(site.button_style) }}
                      />
                      {buttonStyleOptions.find((s) => s.value === site.button_style)?.label ?? site.button_style}
                    </Badge>
                  </div>
                </div>

                {/* Stats row */}
                <div className="flex gap-4 pt-1 border-t text-xs text-slate-500">
                  <div className="flex items-center gap-1">
                    <FileText className="h-3.5 w-3.5" />
                    <span>{countPostsForSite(key)} posts mapped</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <RefreshCw className="h-3.5 w-3.5" />
                    <span>{countAutoUpdateForSite(key)} auto-updating</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-1">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => openEdit(key)}>
                    <Pencil className="mr-1.5 h-3.5 w-3.5" />
                    Edit
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="border-red-200 text-red-600 hover:bg-red-50"
                    onClick={() => setDeleteTarget(key)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* ── Add / Edit Site Dialog ── */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingKey ? "Edit Site" : "Add New Site"}</DialogTitle>
            <DialogDescription>
              {editingKey
                ? `Update settings for "${sites[editingKey]?.display_name ?? editingKey}".`
                : "Connect a new WordPress site to SmartLink Updater."}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-2">
            {/* Site Key */}
            <div className="space-y-1.5">
              <Label>Site Key</Label>
              <Input
                placeholder="my-site"
                value={formKey}
                onChange={(e) => setFormKey(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""))}
                readOnly={!!editingKey}
                className={editingKey ? "bg-slate-50" : ""}
              />
              <p className="text-xs text-slate-500">
                Unique identifier. Lowercase letters, numbers, hyphens, underscores only.
              </p>
            </div>

            {/* Display Name */}
            <div className="space-y-1.5">
              <Label>Display Name</Label>
              <Input
                placeholder="My WordPress Site"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
              />
            </div>

            {/* Base URL */}
            <div className="space-y-1.5">
              <Label>Base URL</Label>
              <Input
                placeholder="https://yoursite.com"
                value={formUrl}
                onChange={(e) => setFormUrl(e.target.value)}
              />
            </div>

            {/* Username */}
            <div className="space-y-1.5">
              <Label>Username</Label>
              <Input
                placeholder="admin"
                value={formUsername}
                onChange={(e) => setFormUsername(e.target.value)}
              />
            </div>

            {/* Application Password */}
            <div className="space-y-1.5">
              <Label>Application Password</Label>
              <div className="flex gap-2">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="xxxx xxxx xxxx xxxx"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  className="font-mono"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-slate-500">
                Generate in WordPress → Users → Application Passwords
              </p>
            </div>

            {/* Button Style */}
            <div className="space-y-1.5">
              <Label>Button Style</Label>
              <Select value={formStyle} onValueChange={setFormStyle}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {buttonStyleOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      <div className="flex items-center gap-2">
                        <span
                          className="inline-block h-3 w-3 rounded-full"
                          style={{ backgroundColor: opt.color }}
                        />
                        {opt.label}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {/* Preview strip */}
              <div
                className="mt-2 h-2 w-full rounded-full"
                style={{
                  background: `linear-gradient(90deg, ${getStyleColor(formStyle)}, ${getStyleColor(formStyle)}66)`,
                }}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              className={`bg-gradient-to-r ${theme.brand.gradient} text-white`}
              disabled={!formKey || !formUrl || !formUsername}
            >
              {editingKey ? "Save Changes" : "Add Site"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Delete Confirmation ── */}
      <AlertDialog open={!!deleteTarget} onOpenChange={() => setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete site &ldquo;{deleteTarget && sites[deleteTarget]?.display_name}&rdquo;?</AlertDialogTitle>
            <AlertDialogDescription>
              This will NOT remove post mappings, but updates to this site will stop.
              You can re-add the site later.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction className="bg-red-600 hover:bg-red-700" onClick={handleDelete}>
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
