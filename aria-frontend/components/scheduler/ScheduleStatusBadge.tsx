// filename: components/scheduler/ScheduleStatusBadge.tsx
// purpose: Scheduling lifecycle badge with retry countdown for dead-letter state.

"use client";

import { useEffect, useMemo, useState } from "react";

import type { ScheduleStatus } from "@/types";

interface Props {
  status: ScheduleStatus;
  retryCount?: number;
  maxRetries?: number;
  nextRetryAt?: string | null;
}

const pad = (n: number) => n.toString().padStart(2, "0");

export const ScheduleStatusBadge = ({ status, retryCount, maxRetries, nextRetryAt }: Props) => {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, []);

  const countdown = useMemo(() => {
    if (status !== "failed" || !nextRetryAt) return null;
    const diffMs = new Date(nextRetryAt).getTime() - now;
    if (diffMs <= 0) return "00:00";
    const totalSeconds = Math.floor(diffMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${pad(minutes)}:${pad(seconds)}`;
  }, [now, nextRetryAt, status]);

  if (status === "queued") {
    return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">Queued</span>;
  }
  if (status === "publishing") {
    return <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">Publishing</span>;
  }
  if (status === "awaiting_approval") {
    return <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700">Awaiting approval</span>;
  }
  if (status === "published") {
    return <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">Published</span>;
  }
  if (status === "failed") {
    return (
      <span className="rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700">
        Failed{typeof retryCount === "number" && typeof maxRetries === "number" ? ` Retry ${retryCount}/${maxRetries}` : ""}
        {countdown ? ` ${countdown}` : ""}
      </span>
    );
  }
  if (status === "dead_letter") {
    return (
      <span className="rounded-full bg-black px-3 py-1 text-xs font-medium text-white">
        Dead letter
      </span>
    );
  }
  return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">Unknown</span>;
};
