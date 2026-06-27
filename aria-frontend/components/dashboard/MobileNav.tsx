"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, FileText, LayoutDashboard, PlusCircle, Settings, ShieldCheck, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { label: "Brand", icon: LayoutDashboard, href: "/dashboard/brand" },
  { label: "AI", icon: Sparkles, href: "/dashboard/ai" },
  { label: "Brain", icon: Brain, href: "/dashboard/brand-brain" },
  { label: "Studio", icon: FileText, href: "/dashboard/content-studio" },
  { label: "Create", icon: PlusCircle, href: "/dashboard/create" },
  { label: "Approval", icon: ShieldCheck, href: "/dashboard/approval" },
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
