"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  Calendar,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  Grid,
  LayoutDashboard,
  LogOut,
  PlusCircle,
  Settings
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/context/AuthContext";
import { useDashboardStore } from "@/lib/store";
import { cn } from "@/lib/utils";

const navSections = [
  {
    label: "Main",
    items: [
      { label: "Brand Dashboard", icon: LayoutDashboard, href: "/dashboard/brand" },
      { label: "Analytics", icon: BarChart2, href: "/dashboard/analytics" }
    ]
  },
  {
    label: "Content",
    items: [
      { label: "Content", icon: FileText, href: "/dashboard/content" },
      { label: "Create Post", icon: PlusCircle, href: "/dashboard/create", highlight: true },
      { label: "Posts", icon: Grid, href: "/dashboard/posts" },
      { label: "Scheduler", icon: Calendar, href: "/dashboard/scheduler" }
    ]
  },
  {
    label: "Settings",
    items: [{ label: "Settings", icon: Settings, href: "/dashboard/settings" }]
  }
] as const;

const getInitials = (name: string | null | undefined): string => {
  if (!name) {
    return "AR";
  }
  return name
    .split(" ")
    .map((token) => token[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
};

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const isCollapsed = useDashboardStore((state) => state.sidebarCollapsed);
  const setCollapsed = useDashboardStore((state) => state.setSidebarCollapsed);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen flex-col border-r border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_94%,transparent)] px-3 py-4 backdrop-blur lg:flex transition-all duration-300",
        isCollapsed ? "w-16" : "w-60"
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <Link href="/dashboard/brand" className={cn("font-black tracking-tight text-transparent bg-gradient-to-r from-teal-500 to-sky-500 bg-clip-text", isCollapsed ? "text-lg" : "text-2xl")}>ARIA</Link>
        <Button variant="ghost" size="icon" onClick={() => setCollapsed(!isCollapsed)} aria-label="Toggle sidebar">
          {isCollapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
        </Button>
      </div>

      <div className="space-y-4 overflow-y-auto pb-4">
        {navSections.map((section) => (
          <div key={section.label} className="space-y-1">
            {!isCollapsed ? <p className="label-xs px-2">{section.label}</p> : null}
            {section.items.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const isHighlighted = "highlight" in item && item.highlight;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "group flex items-center rounded-lg border-l-2 px-2 py-2 text-sm transition-all",
                    active
                      ? "border-l-[var(--brand-primary)] bg-[var(--bg-elevated)] text-[var(--text-primary)]"
                      : "border-l-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]",
                    isHighlighted && !active ? "text-[var(--brand-primary)]" : ""
                  )}
                >
                  <item.icon className="h-4 w-4 shrink-0" />
                  {!isCollapsed ? <span className="ml-2 truncate">{item.label}</span> : null}
                </Link>
              );
            })}
            <Separator className="mt-3" />
          </div>
        ))}
      </div>

      <div className="mt-auto space-y-2 rounded-xl border border-[var(--border)] p-2">
        <div className="flex items-center gap-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback>{getInitials(user?.name)}</AvatarFallback>
          </Avatar>
          {!isCollapsed ? (
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{user?.name ?? "ARIA User"}</p>
              <p className="truncate text-xs text-[var(--text-muted)]">{user?.email ?? "user@aria.ai"}</p>
            </div>
          ) : null}
        </div>
        <Button variant="ghost" size="sm" className={cn("w-full justify-start", isCollapsed ? "px-0 justify-center" : "")} onClick={logout}>
          <LogOut className="h-4 w-4" />
          {!isCollapsed ? <span>Logout</span> : null}
        </Button>
      </div>
    </aside>
  );
}
