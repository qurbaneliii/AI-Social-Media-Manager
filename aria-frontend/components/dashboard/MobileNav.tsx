"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Calendar, FileText, LayoutDashboard, PlusCircle, Settings } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { label: "Brand", icon: LayoutDashboard, href: "/dashboard/brand" },
  { label: "Content", icon: FileText, href: "/dashboard/content" },
  { label: "Create", icon: PlusCircle, href: "/dashboard/create" },
  { label: "Analytics", icon: BarChart2, href: "/dashboard/analytics" },
  { label: "More", icon: Calendar, href: "/dashboard/scheduler" },
  { label: "Settings", icon: Settings, href: "/dashboard/settings" }
] as const;

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_92%,transparent)] p-2 backdrop-blur lg:hidden">
      {navItems.map((item) => {
        const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex min-w-12 flex-col items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium",
              active ? "text-[var(--brand-primary)]" : "text-[var(--text-muted)]"
            )}
          >
            <item.icon className="h-4 w-4" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
