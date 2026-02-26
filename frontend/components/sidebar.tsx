"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  GitBranch,
  Bell,
  BarChart3,
  Globe,
  Settings,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { theme } from "@/lib/theme";
import { unreadAlertCount } from "@/lib/mock-data";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: "Home", href: "/", icon: LayoutDashboard },
  { label: "Posts", href: "/posts", icon: FileText },
  { label: "Batches", href: "/batches", icon: GitBranch },
  { label: "Alerts", href: "/alerts", icon: Bell, badge: unreadAlertCount },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Sites", href: "/sites", icon: Globe },
  { label: "Settings", href: "/settings", icon: Settings },
];

function NavItemLink({
  item,
  collapsed,
  onClick,
}: {
  item: NavItem;
  collapsed: boolean;
  onClick?: () => void;
}) {
  const pathname = usePathname();
  const isActive =
    item.href === "/"
      ? pathname === "/"
      : pathname.startsWith(item.href);
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
        theme.nav.text,
        isActive && `${theme.nav.activeItem} ${theme.nav.activeText}`,
        !isActive && `hover:${theme.nav.hoverItem} hover:${theme.nav.activeText}`,
        collapsed && "justify-center px-2"
      )}
      title={collapsed ? item.label : undefined}
    >
      <Icon className="h-5 w-5 shrink-0" />
      {!collapsed && (
        <span className="truncate">{item.label}</span>
      )}
      {!collapsed && item.badge && item.badge > 0 && (
        <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-semibold text-white">
          {item.badge}
        </span>
      )}
      {collapsed && item.badge && item.badge > 0 && (
        <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
          {item.badge}
        </span>
      )}
    </Link>
  );
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className={cn(
          "fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-lg lg:hidden",
          theme.nav.bg,
          "text-white"
        )}
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-[260px] flex-col lg:hidden",
          theme.nav.bg,
          "transform transition-transform duration-200 ease-in-out",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#667eea] to-[#764ba2]">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold text-white">SmartLink</span>
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:text-white"
            aria-label="Close navigation menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavItemLink
              key={item.href}
              item={item}
              collapsed={false}
              onClick={() => setMobileOpen(false)}
            />
          ))}
        </nav>

        <div className="border-t border-white/10 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-xs text-slate-400">API Connected</span>
          </div>
        </div>
      </aside>

      {/* Desktop sidebar */}
      <aside
        className={cn(
          "hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:z-30",
          theme.nav.bg,
          "transition-all duration-200 ease-in-out",
          collapsed ? "lg:w-16" : "lg:w-[260px]"
        )}
      >
        {/* Logo */}
        <div
          className={cn(
            "flex h-16 items-center",
            collapsed ? "justify-center px-2" : "px-4"
          )}
        >
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-[#667eea] to-[#764ba2]">
              <Zap className="h-4 w-4 text-white" />
            </div>
            {!collapsed && (
              <span className="text-lg font-bold text-white">SmartLink</span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <div key={item.href} className="relative">
              <NavItemLink item={item} collapsed={collapsed} />
            </div>
          ))}
        </nav>

        {/* Bottom section */}
        <div className="border-t border-white/10 px-3 py-3">
          <div
            className={cn(
              "flex items-center",
              collapsed ? "justify-center" : "justify-between"
            )}
          >
            {!collapsed && (
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-xs text-slate-400">API Connected</span>
              </div>
            )}
            {collapsed && (
              <span className="mb-2 h-2 w-2 rounded-full bg-emerald-500" title="API Connected" />
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className={cn(
              "flex w-full items-center rounded-lg px-2 py-2 text-slate-400 transition-colors hover:text-white",
              collapsed ? "justify-center" : "justify-end"
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
