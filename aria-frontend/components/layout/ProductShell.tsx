"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { MobileNav } from "@/components/dashboard/MobileNav";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { TopBar } from "@/components/dashboard/TopBar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/context/AuthContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { getDefaultRouteForRole, getNavigationItems, isActiveRoute } from "@/lib/navigation";
import { navigateTo } from "@/lib/navigate";

interface ProductShellProps {
  children: React.ReactNode;
}

export function ProductShell({ children }: ProductShellProps) {
  const pathname = usePathname();
  const reduceMotion = useReducedMotion();
  const { user } = useAuth();
  const { isLoading } = useRequireAuth();

  useEffect(() => {
    if (isLoading || !user) {
      return;
    }

    const allowed = getNavigationItems(user.role).some((item) => isActiveRoute(pathname, item.href));
    if (!allowed) {
      navigateTo(getDefaultRouteForRole(user.role));
    }
  }, [isLoading, pathname, user]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-[var(--bg-base)] p-4 sm:p-6" aria-busy="true" aria-label="Loading workspace">
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <Skeleton className="hidden h-[calc(100vh-3rem)] lg:block" />
          <div className="space-y-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-24" />
            <Skeleton className="h-64" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid="aria-product-shell"
      className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] lg:flex"
    >
      <Sidebar />
      <div className="min-w-0 flex-1">
        <TopBar />
        <AnimatePresence mode="wait" initial={false}>
          <motion.main
            id="aria-product-content"
            key={pathname}
            initial={reduceMotion ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -4 }}
            transition={{ duration: reduceMotion ? 0 : 0.16 }}
            className="mx-auto w-full max-w-[1600px] px-4 pb-24 pt-4 sm:px-6 sm:pt-6 lg:pb-8 xl:px-8"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>
      <MobileNav />
    </div>
  );
}
