"use client";

import { motion, type Variants } from "framer-motion";
import { BarChart3, Clock3, Eye, FileText, Send, TrendingUp } from "lucide-react";

import { AIGeneratorPanel } from "@/components/dashboard/AIGeneratorPanel";
import { BrandProfileCard } from "@/components/dashboard/BrandProfileCard";
import { NotificationItem } from "@/components/dashboard/NotificationItem";
import { PlatformPieChart } from "@/components/dashboard/PlatformPieChart";
import { PostCard } from "@/components/dashboard/PostCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { WeeklyChart } from "@/components/dashboard/WeeklyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/useDashboard";
import { useDashboardStore } from "@/lib/store";

const iconMap = {
  FileText,
  Clock3,
  Send,
  TrendingUp,
  Eye,
  BarChart3
} as const;

const iconColorMap = {
  FileText: "bg-teal-500/15 text-teal-700",
  Clock3: "bg-sky-500/15 text-sky-700",
  Send: "bg-violet-500/15 text-violet-700",
  TrendingUp: "bg-emerald-500/15 text-emerald-700",
  Eye: "bg-blue-500/15 text-blue-700",
  BarChart3: "bg-amber-500/15 text-amber-700"
} as const;

const containerVariants: Variants = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.08
    }
  }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

export default function BrandDashboardPage() {
  const { isLoading, statMetrics, weeklyPerformance, platformBreakdown, notifications, posts, brandProfile } = useDashboard();
  const markNotificationRead = useDashboardStore((state) => state.markNotificationRead);
  const dismissNotification = useDashboardStore((state) => state.dismissNotification);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16" />
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-44" />
          ))}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-[460px] lg:col-span-2" />
          <Skeleton className="h-[460px]" />
        </div>
      </div>
    );
  }

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="space-y-6">
      <motion.section variants={itemVariants} className="space-y-1">
        <h1>Brand Dashboard</h1>
        <p className="text-sm text-[var(--text-secondary)]">Central command center for AI-assisted publishing and growth analytics.</p>
      </motion.section>

      <motion.section variants={itemVariants} className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {statMetrics.map((metric, index) => {
          const Icon = iconMap[metric.icon];
          return (
            <StatCard
              key={metric.id}
              title={metric.title}
              value={metric.value}
              valuePrefix={metric.valuePrefix}
              valueSuffix={metric.valueSuffix}
              change={metric.change}
              changeLabel={metric.changeLabel}
              icon={Icon}
              iconColor={iconColorMap[metric.icon]}
              trend={metric.trend}
              index={index}
            />
          );
        })}
      </motion.section>

      <motion.section variants={itemVariants} className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AIGeneratorPanel />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {notifications.length ? (
              notifications.map((item) => (
                <NotificationItem
                  key={item.id}
                  notification={item}
                  onRead={markNotificationRead}
                  onDismiss={dismissNotification}
                />
              ))
            ) : (
              <p className="py-12 text-center text-sm text-[var(--text-muted)]">No notifications.</p>
            )}
          </CardContent>
        </Card>
      </motion.section>

      <motion.section variants={itemVariants} className="space-y-3">
        <div className="flex items-center justify-between">
          <h2>Recent Posts</h2>
          <p className="text-xs text-[var(--text-muted)]">Scroll horizontally</p>
        </div>

        <div className="-mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
          {posts.map((post) => (
            <PostCard key={post.id} {...post} />
          ))}
        </div>
      </motion.section>

      <motion.section variants={itemVariants} className="grid gap-4 xl:grid-cols-2">
        <WeeklyChart data={weeklyPerformance} />
        <PlatformPieChart data={platformBreakdown} />
      </motion.section>

      <motion.section variants={itemVariants}>
        <BrandProfileCard profile={brandProfile} />
      </motion.section>
    </motion.div>
  );
}
