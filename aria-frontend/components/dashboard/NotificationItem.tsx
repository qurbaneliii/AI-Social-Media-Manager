"use client";

import { useState } from "react";
import { AlertTriangle, Bell, CheckCircle2, X, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import type { DashboardNotification, NotificationType } from "@/lib/mock-data";

interface NotificationItemProps {
  notification: DashboardNotification;
  onRead: (id: string) => void;
  onDismiss: (id: string) => void;
}

const iconStyles: Record<NotificationType, string> = {
  info: "bg-blue-500",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500"
};

const iconMap = {
  info: Bell,
  success: CheckCircle2,
  warning: AlertTriangle,
  error: XCircle
} as const;

const relativeTime = (iso: string): string => {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) {
    return `${mins} minutes ago`;
  }
  const hours = Math.floor(mins / 60);
  if (hours < 24) {
    return `${hours} hours ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days} days ago`;
};

export function NotificationItem({ notification, onRead, onDismiss }: NotificationItemProps) {
  const [hovered, setHovered] = useState(false);

  const Icon = iconMap[notification.type];

  return (
    <button
      type="button"
      onClick={() => onRead(notification.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        "group relative flex w-full items-start gap-3 overflow-hidden rounded-xl border border-[var(--border)] px-3 py-3 text-left transition",
        notification.read ? "bg-transparent" : "bg-[color-mix(in_srgb,var(--bg-elevated)_70%,transparent)]"
      )}
    >
      <span className={cn("absolute inset-y-0 left-0 w-1", iconStyles[notification.type])} />
      <span className="mt-0.5 grid h-8 w-8 place-items-center rounded-lg bg-[var(--bg-elevated)]">
        <Icon className="h-4 w-4 text-[var(--text-secondary)]" />
      </span>

      <span className="min-w-0 flex-1">
        <span className="flex items-start justify-between gap-2">
          <span className="truncate text-sm font-semibold">{notification.title}</span>
          <span className="text-xs text-[var(--text-muted)]">{relativeTime(notification.timestamp)}</span>
        </span>
        <span className="mt-1 block text-xs leading-5 text-[var(--text-secondary)]">{notification.message}</span>
      </span>

      {!notification.read ? <span className="absolute right-3 top-3 h-2.5 w-2.5 rounded-full bg-[var(--brand-primary)]" /> : null}

      {hovered ? (
        <span
          role="button"
          tabIndex={0}
          onClick={(event) => {
            event.stopPropagation();
            onDismiss(notification.id);
          }}
          className="absolute bottom-2 right-2 grid h-6 w-6 place-items-center rounded-md text-[var(--text-muted)] hover:bg-[var(--bg-elevated)]"
        >
          <X className="h-3.5 w-3.5" />
        </span>
      ) : null}
    </button>
  );
}
