"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, Check, Clock3, Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { SkeletonBlock } from "@/components/ui/SkeletonBlock";
import { approveSchedule, listCalendarItems, listUnscheduledContent } from "@/lib/api";

function formatRunTime(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function stateLabel(value: string) {
  return value.replaceAll("_", " ");
}

export default function SchedulerPage() {
  const queryClient = useQueryClient();
  const [platformFilter, setPlatformFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const browserTimezone = useMemo(() => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC", []);
  const previewMode = process.env.NEXT_PUBLIC_PREVIEW_MODE === "true";
  const calendarQuery = useQuery({
    queryKey: ["calendar", platformFilter, statusFilter],
    queryFn: () => listCalendarItems({ platform: platformFilter, planning_state: statusFilter })
  });
  const unscheduledQuery = useQuery({ queryKey: ["calendar", "unscheduled"], queryFn: listUnscheduledContent });
  const approveMutation = useMutation({
    mutationFn: approveSchedule,
    onSuccess: async () => {
      toast.success("Plan approved for internal readiness");
      await queryClient.invalidateQueries({ queryKey: ["calendar"] });
    },
    onError: () => toast.error("Internal approval failed")
  });

  const items = calendarQuery.data ?? [];
  const awaitingApproval = items.filter((item) => item.approval_status === "in_review").length;
  const approvedInternal = items.filter((item) => item.planning_state === "approved_internal").length;

  return (
    <section className="mx-auto w-full max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="label-xs mb-2">Internal planning</p>
          <h1>Calendar</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">
            Plan approved content inside ARIA. No item on this page is externally scheduled or published.
          </p>
        </div>
        <Link href="/posts/new" className="inline-flex min-h-11 items-center justify-center gap-2 rounded bg-teal-700 px-4 text-sm font-semibold text-white hover:bg-teal-800">
          <Plus aria-hidden="true" className="size-4" /> Create content
        </Link>
      </header>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded border border-sky-200 bg-sky-50 px-2 py-1 font-semibold text-sky-800">{previewMode ? "Demo planning data" : "Workspace data"}</span>
        <span className="text-[var(--text-secondary)]">Source: {previewMode ? "static preview records" : "persisted internal planning records"}</span>
        <span className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-2 py-1 font-semibold text-[var(--text-secondary)]">Timezone: {browserTimezone}</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2" aria-label="Calendar filters">
        <label>
          <span className="sr-only">Filter calendar by platform</span>
          <select value={platformFilter} onChange={(event) => setPlatformFilter(event.target.value)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm">
            <option value="all">All platforms</option><option value="instagram">Instagram</option><option value="linkedin">LinkedIn</option><option value="facebook">Facebook</option><option value="x">X</option><option value="tiktok">TikTok</option><option value="pinterest">Pinterest</option>
          </select>
        </label>
        <label>
          <span className="sr-only">Filter calendar by status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm">
            <option value="all">All planning states</option><option value="draft_plan">Draft plan</option><option value="awaiting_approval">Awaiting approval</option><option value="approved_internal">Approved internally</option><option value="ready_for_scheduling">Ready for future integration</option><option value="failed">Failed</option>
          </select>
        </label>
      </div>

      <dl className="grid border-y border-[var(--border)] sm:grid-cols-3">
        <div className="py-4 sm:pr-6"><dt className="label-xs">Internal plans</dt><dd className="mt-1 text-2xl font-bold">{items.length}</dd></div>
        <div className="border-t border-[var(--border)] py-4 sm:border-l sm:border-t-0 sm:px-6"><dt className="label-xs">Awaiting approval</dt><dd className="mt-1 text-2xl font-bold text-amber-700">{awaitingApproval}</dd></div>
        <div className="border-t border-[var(--border)] py-4 sm:border-l sm:border-t-0 sm:pl-6"><dt className="label-xs">Approved internally</dt><dd className="mt-1 text-2xl font-bold text-emerald-700">{approvedInternal}</dd></div>
      </dl>

      {calendarQuery.isLoading ? <div className="space-y-3" aria-live="polite"><SkeletonBlock className="h-28 w-full rounded" /><SkeletonBlock className="h-28 w-full rounded" /></div> : null}
      {calendarQuery.isError ? (
        <div className="flex flex-col gap-3 rounded border border-red-200 bg-red-50 p-5 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between" role="alert">
          <span className="flex items-center gap-2"><AlertTriangle aria-hidden="true" className="size-5" /> Calendar records could not be loaded.</span>
          <button type="button" onClick={() => calendarQuery.refetch()} className="inline-flex min-h-11 items-center justify-center gap-2 rounded border border-red-300 px-3 font-semibold"><RefreshCw aria-hidden="true" className="size-4" /> Retry</button>
        </div>
      ) : null}
      {!calendarQuery.isLoading && !calendarQuery.isError && items.length === 0 ? (
        <div className="surface-card flex flex-col items-center rounded px-5 py-14 text-center">
          <CalendarClock aria-hidden="true" className="mb-4 size-9 text-[var(--text-muted)]" />
          <h2>No internal plans match these filters</h2>
          <p className="mt-2 max-w-md text-sm text-[var(--text-secondary)]">Choose unscheduled content below or create a new draft.</p>
        </div>
      ) : null}

      <div className="space-y-3" aria-live="polite">
        {items.map((item) => (
          <article key={item.calendar_item_id} className="surface-card rounded p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 space-y-2">
                <div className="flex flex-wrap items-center gap-2"><h2 className="text-base capitalize">{item.platform} content plan</h2><span className="rounded border border-[var(--border)] px-2 py-1 text-xs capitalize">{stateLabel(item.planning_state)}</span><span className="rounded border border-[var(--border)] px-2 py-1 text-xs capitalize">Approval: {stateLabel(item.approval_status)}</span></div>
                <p className="text-sm text-[var(--text-secondary)]">{item.topic || "Planned content"}</p>
                <p className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><Clock3 aria-hidden="true" className="size-4" /> {formatRunTime(item.planned_at)} ({item.timezone || "UTC"})</p>
              </div>
              {item.planning_state === "draft_plan" ? <button type="button" disabled={approveMutation.isPending} onClick={() => approveMutation.mutate(item.calendar_item_id)} className="inline-flex min-h-11 items-center justify-center gap-2 rounded bg-teal-700 px-4 text-sm font-semibold text-white disabled:opacity-60"><Check aria-hidden="true" className="size-4" /> Approve internally</button> : null}
            </div>
          </article>
        ))}
      </div>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="unscheduled-content-heading">
        <div><h2 id="unscheduled-content-heading">Unscheduled content</h2><p className="mt-1 text-sm text-[var(--text-secondary)]">{previewMode ? "Static preview drafts available for internal planning." : "Persisted drafts not yet attached to an internal calendar plan."}</p></div>
        {unscheduledQuery.isLoading ? <p className="py-8 text-sm text-[var(--text-secondary)]">Loading content availability...</p> : null}
        {unscheduledQuery.isError ? <p className="py-8 text-sm text-red-700" role="alert">Unscheduled content is unavailable.</p> : null}
        {!unscheduledQuery.isLoading && !unscheduledQuery.isError && !unscheduledQuery.data?.length ? <p className="py-8 text-sm text-[var(--text-secondary)]">No generated content is waiting for planning.</p> : null}
        <div className="mt-3 divide-y divide-[var(--border)]">
          {unscheduledQuery.data?.map((item) => <article key={item.draft_id} className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div className="min-w-0"><p className="line-clamp-2 text-sm">{item.content_text || item.topic}</p><p className="mt-1 text-xs capitalize text-[var(--text-muted)]">{item.platform} · {stateLabel(item.approval_status)}</p></div><Link href={`/posts/${item.draft_id}/schedule`} className="inline-flex min-h-11 items-center justify-center rounded border border-[var(--border-strong)] px-3 text-sm font-semibold">Plan content</Link></article>)}
        </div>
      </section>
    </section>
  );
}
