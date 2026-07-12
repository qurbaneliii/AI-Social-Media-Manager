"use client";

import { useQueries } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, Check, Clock3, Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { ScheduleStatusBadge } from "@/components/scheduler/ScheduleStatusBadge";
import { SkeletonBlock } from "@/components/ui/SkeletonBlock";
import { RETRY_JITTER_PERCENT, RETRY_SCHEDULE_SECONDS } from "@/config/constants";
import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { approveSchedule, getSchedule, type ScheduleDetail } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { useSchedulerStore } from "@/stores/useSchedulerStore";

function formatRunTime(value: string | null | undefined) {
  if (!value) return "No planning time recorded";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

export default function SchedulerPage() {
  const scheduleIds = useSchedulerStore((state) => state.scheduleIds);
  const [platformFilter, setPlatformFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const companyId = useCompanyStore((state) => state.companyId) ?? getClientSession().companyId;
  const postsQuery = useCompanyPosts(companyId, 0);
  const timezone = useMemo(() => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC", []);
  const scheduleQueries = useQueries({
    queries: scheduleIds.map((id) => ({
      queryKey: ["schedule", id],
      queryFn: () => getSchedule(id),
      enabled: Boolean(id),
      refetchInterval: 10_000
    }))
  });

  const loadedSchedules = scheduleQueries.map((query) => query.data).filter((item): item is ScheduleDetail => Boolean(item));
  const visibleScheduleIds = new Set(
    loadedSchedules
      .filter((item) => {
        const platform = item.platform ?? item.target?.platform ?? "unknown";
        return (platformFilter === "all" || platform === platformFilter) && (statusFilter === "all" || item.status === statusFilter);
      })
      .map((item) => item.id)
  );
  const awaitingApproval = loadedSchedules.filter((item) => item.status === "awaiting_approval").length;
  const needsAttention = loadedSchedules.filter((item) => item.status === "failed" || item.status === "dead_letter").length;

  return (
    <section className="mx-auto w-full max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="label-xs mb-2">Internal planning</p>
          <h1>Calendar</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">Track planning readiness and approvals. Items shown here are not externally published unless a connected platform confirms publication.</p>
        </div>
        <Link href="/posts/new" className="inline-flex min-h-11 items-center justify-center gap-2 rounded bg-teal-700 px-4 text-sm font-semibold text-white hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]">
          <Plus aria-hidden="true" className="size-4" /> Create content
        </Link>
      </header>

      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 font-semibold text-amber-800">Demo planning data</span>
        <span className="text-[var(--text-secondary)]">No live publishing integration is represented on this screen.</span>
        <span className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-2 py-1 font-semibold text-[var(--text-secondary)]">Timezone: {timezone}</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2" aria-label="Calendar filters">
        <label><span className="sr-only">Filter calendar by platform</span><select value={platformFilter} onChange={(event) => setPlatformFilter(event.target.value)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm text-[var(--text-primary)]"><option value="all">All platforms</option><option value="instagram">Instagram</option><option value="linkedin">LinkedIn</option><option value="facebook">Facebook</option><option value="x">X</option><option value="tiktok">TikTok</option><option value="pinterest">Pinterest</option></select></label>
        <label><span className="sr-only">Filter calendar by status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm text-[var(--text-primary)]"><option value="all">All planning statuses</option><option value="queued">Queued</option><option value="awaiting_approval">Awaiting approval</option><option value="approved">Approved</option><option value="failed">Failed</option><option value="dead_letter">Needs manual recovery</option></select></label>
      </div>

      {loadedSchedules.length > 0 ? (
        <dl className="grid border-y border-[var(--border)] sm:grid-cols-3">
          <div className="py-4 sm:pr-6"><dt className="label-xs">Tracked plans</dt><dd className="mt-1 text-2xl font-bold text-[var(--text-primary)]">{loadedSchedules.length}</dd></div>
          <div className="border-t border-[var(--border)] py-4 sm:border-l sm:border-t-0 sm:px-6"><dt className="label-xs">Awaiting approval</dt><dd className="mt-1 text-2xl font-bold text-amber-700">{awaitingApproval}</dd></div>
          <div className="border-t border-[var(--border)] py-4 sm:border-l sm:border-t-0 sm:pl-6"><dt className="label-xs">Needs attention</dt><dd className="mt-1 text-2xl font-bold text-red-700">{needsAttention}</dd></div>
        </dl>
      ) : null}

      {scheduleIds.length === 0 ? (
        <div className="surface-card flex flex-col items-center rounded px-5 py-14 text-center">
          <CalendarClock aria-hidden="true" className="mb-4 size-9 text-[var(--text-muted)]" />
          <h2>No internal plans yet</h2>
          <p className="mt-2 max-w-md text-sm text-[var(--text-secondary)]">Create a content package, review its variants, then add an approved item to your planning queue.</p>
          <Link href="/posts/new" className="mt-5 inline-flex min-h-11 items-center gap-2 rounded border border-[var(--border-strong)] px-4 text-sm font-semibold hover:bg-[var(--bg-hover)]"><Plus aria-hidden="true" className="size-4" /> Create content</Link>
        </div>
      ) : null}

      <div className="space-y-3" aria-live="polite">
        {scheduleQueries.map((query, index) => {
          const scheduleId = scheduleIds[index];
          if (query.data && !visibleScheduleIds.has(query.data.id)) return null;
          if (query.isLoading) {
            return <article key={scheduleId} className="surface-card space-y-3 rounded p-5"><SkeletonBlock className="h-4 w-52 rounded" /><SkeletonBlock className="h-4 w-full rounded" /><span className="sr-only">Loading calendar item</span></article>;
          }
          if (query.isError) {
            return (
              <article key={scheduleId} className="flex flex-col gap-4 rounded border border-red-200 bg-red-50 p-5 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between" role="alert">
                <span className="flex items-center gap-2"><AlertTriangle aria-hidden="true" className="size-5" /> This planning item could not be loaded.</span>
                <button type="button" className="inline-flex min-h-11 items-center justify-center gap-2 rounded border border-red-300 px-3 font-semibold" onClick={() => query.refetch()}><RefreshCw aria-hidden="true" className="size-4" /> Retry</button>
              </article>
            );
          }

          const data = query.data;
          const status = data?.status ?? "failed";
          const retryAt = data?.next_retry_at ?? data?.retry_at ?? null;
          const retryCount = data?.retry_count;
          const maxRetries = data?.max_retries ?? RETRY_SCHEDULE_SECONDS.length;
          const runAt = data?.run_at_utc ?? data?.target?.run_at_utc;
          const platform = data?.platform ?? data?.target?.platform ?? "unknown";

          return (
            <article key={scheduleId} className="surface-card rounded p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-base capitalize">{platform} content plan</h2>
                    <ScheduleStatusBadge status={status} retryCount={retryCount} maxRetries={maxRetries} nextRetryAt={retryAt} />
                  </div>
                  <p className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><Clock3 aria-hidden="true" className="size-4 shrink-0" /> {formatRunTime(runAt)}</p>
                  <p className="text-xs text-[var(--text-muted)]" title={scheduleId}>Planning ID {scheduleId.slice(0, 12)}</p>
                </div>

                {status === "awaiting_approval" ? (
                  <button type="button" className="inline-flex min-h-11 items-center justify-center gap-2 rounded bg-teal-700 px-4 text-sm font-semibold text-white hover:bg-teal-800" onClick={async () => {
                    try { await approveSchedule(scheduleId); toast.success("Plan approved for internal readiness"); query.refetch(); }
                    catch { toast.error("Approval failed"); }
                  }}><Check aria-hidden="true" className="size-4" /> Approve plan</button>
                ) : null}
              </div>

              {status === "failed" ? <p className="mt-4 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">Automatic retry uses +1m, +5m, +15m, +45m, and +120m intervals (+/-{Math.round(RETRY_JITTER_PERCENT * 100)}% jitter).</p> : null}
              {status === "dead_letter" ? <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-xs text-red-800">This item exhausted its retries. {data?.error_message ?? "No diagnostic message was provided."}</p> : null}
            </article>
          );
        })}
      </div>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="unscheduled-content-heading">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="unscheduled-content-heading">Unscheduled content</h2><p className="mt-1 text-sm text-[var(--text-secondary)]">Generated packages available for internal planning.</p></div><span className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-2 py-1 text-xs font-semibold text-[var(--text-secondary)]">Internal content</span></div>
        {postsQuery.isLoading ? <p className="py-8 text-sm text-[var(--text-secondary)]">Loading content availability...</p> : null}
        {!postsQuery.isLoading && !(postsQuery.data?.length) ? <p className="py-8 text-sm text-[var(--text-secondary)]">No generated content is waiting for planning.</p> : null}
        {scheduleIds.length > 0 && postsQuery.data?.length ? <p className="mt-4 rounded border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">The current schedule API does not expose a post ID, so ARIA cannot reliably subtract planned packages from this list. Items are shown as planning candidates, not confirmed unscheduled records.</p> : null}
        <div className="mt-3 divide-y divide-[var(--border)]">
          {postsQuery.data?.slice(0, 6).map((post) => {
            const variant = post.generated_package_json?.variants?.[0];
            return <article key={post.post_id} className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"><div className="min-w-0"><p className="line-clamp-2 text-sm text-[var(--text-primary)]">{variant?.text || "Generated content package"}</p><p className="mt-1 text-xs capitalize text-[var(--text-muted)]">{variant?.platform ?? "Platform not selected"} · {post.status}</p></div><Link href={`/posts/${post.post_id}/schedule`} className="inline-flex min-h-11 items-center justify-center rounded border border-[var(--border-strong)] px-3 text-sm font-semibold hover:bg-[var(--bg-hover)]">Plan content</Link></article>;
          })}
        </div>
      </section>
    </section>
  );
}
