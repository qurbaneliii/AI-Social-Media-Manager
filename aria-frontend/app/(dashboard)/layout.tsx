// filename: app/(dashboard)/layout.tsx
// purpose: Dashboard shell with role-aware navigation and route guards.

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import { BarChart3, CalendarClock, FileText, LogOut, PlusCircle } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import type { UserRole } from "@/types";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const roleNav: Record<UserRole, NavItem[]> = {
  agency_admin: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ],
  brand_manager: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ],
  content_creator: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> }
  ],
  analyst: [
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ]
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { isLoading } = useRequireAuth();

  const activeRole = user?.role ?? null;

  const navItems = useMemo(() => {
    if (!activeRole) {
      return [];
    }
    return roleNav[activeRole];
  }, [activeRole]);

  useEffect(() => {
    if (isLoading || !activeRole) {
      return;
    }
    const allowed = roleNav[activeRole].some((item) => pathname.startsWith(item.href));
    if (!allowed) {
      const fallback = roleNav[activeRole][0]?.href ?? "/posts";
      router.replace(fallback);
    }
  }, [activeRole, isLoading, pathname, router]);

  if (isLoading) {
    return <div className="min-h-screen bg-slate-50 px-4 py-8 text-sm text-slate-600">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500">ARIA</p>
            <p className="text-sm font-semibold text-slate-800">Role: {activeRole ?? "loading"}</p>
          </div>
          <button
            type="button"
            onClick={async () => {
              await logout();
              router.push("/login");
            }}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-700"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-xl border border-slate-200 bg-white p-3">
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  pathname.startsWith(item.href) ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}
