// filename: hooks/useDashboardFeed.ts
// purpose: Real dashboard feed layer sourced from backend posts and audit endpoints.

"use client";

import { useEffect, useMemo } from "react";

import { useAuditLog } from "@/hooks/useAuditLog";
import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getClientSession } from "@/lib/client-session";
import { useDashboardStore } from "@/lib/store";
import { titleCase } from "@/lib/utils";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { DashboardNotification, DashboardPlatform, DashboardPost, PostStatus } from "@/lib/mock-data";

const toDashboardPlatform = (value: unknown): DashboardPlatform => {
  const normalized = String(value ?? "linkedin").toLowerCase();
  if (normalized === "x" || normalized === "twitter") {
    return "twitter";
  }
  if (normalized === "instagram" || normalized === "facebook" || normalized === "linkedin") {
    return normalized;
  }
  return "linkedin";
};

const toDashboardStatus = (value: unknown): PostStatus => {
  const normalized = String(value ?? "draft").toLowerCase();
  if (normalized === "scheduled") {
    return "scheduled";
  }
  if (normalized === "published") {
    return "published";
  }
  if (normalized === "failed") {
    return "failed";
  }
  return "draft";
};

const extractPostContent = (row: any): string => {
  const generated = row?.generated_package_json;
  const variants = Array.isArray(generated?.variants) ? generated.variants : [];
  const selectedVariantId = generated?.selected_variant_id;

  const selectedVariant =
    variants.find((variant: any) => String(variant?.variant_id ?? "") === String(selectedVariantId ?? "")) ?? variants[0];

  const text = selectedVariant?.text ?? row?.core_message ?? "";
  const cleaned = String(text).trim();
  return cleaned || "No content available.";
};

const mapPost = (row: any): DashboardPost => {
  const platformTargets = Array.isArray(row?.platform_targets) ? row.platform_targets : [];
  const platform = toDashboardPlatform(platformTargets[0]);
  const status = toDashboardStatus(row?.status);
  const performance = row?.performance_metrics ?? {};

  return {
    id: String(row?.post_id ?? `post-${Math.random().toString(36).slice(2)}`),
    platform,
    status,
    content: extractPostContent(row),
    scheduledAt: typeof row?.requested_publish_at === "string" ? row.requested_publish_at : undefined,
    metrics: {
      likes: Number(performance.likes ?? performance.reactions ?? 0),
      comments: Number(performance.comments ?? 0),
      shares: Number(performance.shares ?? 0)
    }
  };
};

const mapNotificationType = (action: string): DashboardNotification["type"] => {
  if (/(fail|error|dead|reject)/i.test(action)) {
    return "error";
  }
  if (/(warn|retry|pending)/i.test(action)) {
    return "warning";
  }
  if (/(publish|approve|create|generate|saved|success)/i.test(action)) {
    return "success";
  }
  return "info";
};

const mapNotification = (item: any, index: number): DashboardNotification => {
  const action = String(item?.action ?? "system_event");
  const resourceType = String(item?.resource_type ?? "system");
  const actor = item?.actor ? String(item.actor) : "system";

  return {
    id: String(item?.audit_id ?? `${item?.created_at ?? Date.now()}-${index}`),
    type: mapNotificationType(action),
    title: titleCase(action.replace(/[_-]+/g, " ")),
    message: `${titleCase(resourceType.replace(/[_-]+/g, " "))} update by ${actor}`,
    timestamp: String(item?.created_at ?? new Date().toISOString()),
    read: false
  };
};

export const useDashboardFeed = () => {
  const companyId = useCompanyStore((state) => state.companyId) ?? getClientSession().companyId;

  const setPosts = useDashboardStore((state) => state.setPosts);
  const hydrateNotifications = useDashboardStore((state) => state.hydrateNotifications);
  const clearDashboardData = useDashboardStore((state) => state.clearDashboardData);

  const posts = useDashboardStore((state) => state.posts);
  const notifications = useDashboardStore((state) => state.notifications);

  const postsQuery = useCompanyPosts(companyId, 0);
  const auditQuery = useAuditLog(companyId, 0, 40);

  const mappedPosts = useMemo(() => (postsQuery.data ?? []).map(mapPost), [postsQuery.data]);
  const mappedNotifications = useMemo(() => (auditQuery.data ?? []).map(mapNotification), [auditQuery.data]);

  useEffect(() => {
    if (!companyId) {
      clearDashboardData();
      return;
    }
    setPosts(mappedPosts);
  }, [clearDashboardData, companyId, mappedPosts, setPosts]);

  useEffect(() => {
    if (!companyId) {
      return;
    }
    hydrateNotifications(mappedNotifications);
  }, [companyId, hydrateNotifications, mappedNotifications]);

  const unreadCount = useMemo(() => notifications.filter((item) => !item.read).length, [notifications]);

  return {
    companyId,
    hasCompanyId: Boolean(companyId),
    posts,
    notifications,
    unreadCount,
    isLoading: Boolean(companyId) && (postsQuery.isLoading || auditQuery.isLoading),
    isFetching: Boolean(companyId) && (postsQuery.isFetching || auditQuery.isFetching),
    postsError: postsQuery.error,
    notificationsError: auditQuery.error
  };
};
