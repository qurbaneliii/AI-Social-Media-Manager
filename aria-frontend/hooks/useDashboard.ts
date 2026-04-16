"use client";

import { useEffect, useMemo, useState } from "react";

import { platformBreakdown, statMetrics, weeklyPerformance } from "@/lib/mock-data";
import { useDashboardStore } from "@/lib/store";
import { useDashboardFeed } from "@/hooks/useDashboardFeed";

export const useDashboard = () => {
  const [minDelayDone, setMinDelayDone] = useState(false);

  const feed = useDashboardFeed();

  const notifications = useDashboardStore((state) => state.notifications);
  const posts = useDashboardStore((state) => state.posts);
  const brandProfile = useDashboardStore((state) => state.brandProfile);

  useEffect(() => {
    const timer = window.setTimeout(() => setMinDelayDone(true), 800);
    return () => window.clearTimeout(timer);
  }, []);

  const unreadCount = useMemo(() => notifications.filter((item) => !item.read).length, [notifications]);
  const isLoading = !minDelayDone || feed.isLoading;

  return {
    companyId: feed.companyId,
    hasCompanyId: feed.hasCompanyId,
    isLoading,
    isFetching: feed.isFetching,
    statMetrics,
    weeklyPerformance,
    platformBreakdown,
    notifications,
    unreadCount,
    posts,
    brandProfile,
    postsError: feed.postsError,
    notificationsError: feed.notificationsError
  };
};
