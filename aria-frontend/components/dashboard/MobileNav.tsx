"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/context/AuthContext";
import {
  getMobileMoreNavigationItems,
  getMobileNavigationItems,
  isActiveRoute
} from "@/lib/navigation";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

export function MobileNav() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [moreOpen, setMoreOpen] = useState(false);
  const navItems = getMobileNavigationItems(user?.role ?? null);
  const moreItems = getMobileMoreNavigationItems(user?.role ?? null);
  const moreActive = moreItems.some((item) => isActiveRoute(pathname, item.href));

  return (
    <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
      <nav
        aria-label="Primary mobile navigation"
        className="fixed inset-x-0 bottom-0 z-40 flex items-center justify-around border-t border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-surface)_92%,transparent)] p-2 backdrop-blur lg:hidden"
      >
        {navItems.map((item) => {
          const isMore = item.id === "more";
          const active = isMore ? moreActive : isActiveRoute(pathname, item.href);
          const Icon = item.icon;

          if (isMore) {
            return (
              <SheetTrigger asChild key={item.id}>
                <button
                  type="button"
                  aria-label="Open more navigation"
                  aria-haspopup="dialog"
                  aria-expanded={moreOpen}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 min-w-14 flex-col items-center justify-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-primary)]",
                    active ? "text-[var(--brand-primary)]" : "text-[var(--text-muted)]"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </button>
              </SheetTrigger>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 min-w-14 flex-col items-center justify-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-primary)]",
                active ? "text-[var(--brand-primary)]" : "text-[var(--text-muted)]"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <SheetContent side="bottom" className="max-h-[75vh] overflow-y-auto rounded-t-2xl pb-8 lg:hidden">
        <SheetHeader>
          <SheetTitle>More</SheetTitle>
          <SheetDescription className="sr-only">Secondary ARIA workspace destinations.</SheetDescription>
        </SheetHeader>
        <nav className="mt-5 grid gap-2" aria-label="More navigation destinations">
          {moreItems.map((item) => {
            const active = isActiveRoute(pathname, item.href);
            const Icon = item.icon;
            return (
              <SheetClose asChild key={item.href}>
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 items-center gap-3 rounded-lg border px-3 py-2 text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-primary)]",
                    active
                      ? "border-[var(--brand-primary)] bg-[var(--bg-elevated)] text-[var(--text-primary)]"
                      : "border-[var(--border)] text-[var(--text-secondary)]"
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span>{item.label}</span>
                </Link>
              </SheetClose>
            );
          })}
        </nav>
      </SheetContent>
    </Sheet>
  );
}
