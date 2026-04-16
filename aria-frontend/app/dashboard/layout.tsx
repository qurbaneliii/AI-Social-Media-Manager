"use client";

import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";

import { MobileNav } from "@/components/dashboard/MobileNav";
import { Sidebar } from "@/components/dashboard/Sidebar";
import { TopBar } from "@/components/dashboard/TopBar";
import { Skeleton } from "@/components/ui/skeleton";
import { useRequireAuth } from "@/hooks/useRequireAuth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isLoading } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen p-6">
        <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
          <Skeleton className="hidden h-[85vh] lg:block" />
          <div className="space-y-4">
            <Skeleton className="h-16" />
            <Skeleton className="h-40" />
            <Skeleton className="h-72" />
            <Skeleton className="h-72" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <TopBar />
        <AnimatePresence mode="wait">
          <motion.main
            key={pathname}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.25 }}
            className="px-4 pb-24 pt-4 sm:px-6 sm:pt-6 lg:pb-8"
          >
            {children}
          </motion.main>
        </AnimatePresence>
      </div>
      <MobileNav />
    </div>
  );
}
