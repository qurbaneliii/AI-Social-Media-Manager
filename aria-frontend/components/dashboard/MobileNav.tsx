"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import { getMobileNavigationItems, isActiveRoute } from "@/lib/navigation";
import { cn } from "@/lib/utils";

export function MobileNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const navItems = getMobileNavigationItems(user?.role ?? null);

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_92%,transparent)] p-2 backdrop-blur lg:hidden">
      {navItems.map((item) => {
        const active = isActiveRoute(pathname, item.href);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex min-w-14 flex-col items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium",
              active ? "text-[var(--brand-primary)]" : "text-[var(--text-muted)]"
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
