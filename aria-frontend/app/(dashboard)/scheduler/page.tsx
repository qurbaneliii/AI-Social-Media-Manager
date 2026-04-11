// filename: app/(dashboard)/scheduler/page.tsx
// purpose: Scheduler queue with status lifecycle and approval actions.

"use client";

import { useQueries } from "@tanstack/react-query";
import { toast } from "sonner";

import { ScheduleStatusBadge } from "@/components/scheduler/ScheduleStatusBadge";
import { RETRY_JITTER_PERCENT, RETRY_SCHEDULE_SECONDS } from "@/config/constants";
import { approveSchedule, getSchedule } from "@/lib/api";
import { useSchedulerStore } from "@/stores/useSchedulerStore";

export default function SchedulerPage() {
  const scheduleIds = useSchedulerStore((s) => s.scheduleIds);

  const scheduleQueries = useQueries({
    queries: scheduleIds.map((id) => ({
      queryKey: ["schedule", id],
      queryFn: () => getSchedule(id),
      enabled: Boolean(id),
      refetchInterval: 10_000
    }))
  });

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Scheduler</h1>
        <p className="text-sm text-slate-600">Track scheduled posts and resolve approval or retry states.</p>
      </header>

      {scheduleIds.length === 0 ? <p className="text-sm text-slate-600">No scheduled jobs yet.</p> : null}

      <div className="space-y-3">
        {scheduleQueries.map((query, idx) => {
          const scheduleId = scheduleIds[idx];
          if (query.isLoading) {
            return (
              <article key={scheduleId} className="rounded-xl border p-4 text-sm text-slate-500">
                Loading {scheduleId}...
              </article>
            );
          }
          if (query.isError) {
            return (
              <article key={scheduleId} className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                Failed to load schedule {scheduleId}
              </article>
            );
          }

          const data = query.data as any;
          const status = (data?.status ?? "failed") as any;
          const retryAt = data?.next_retry_at ?? data?.retry_at ?? null;
          const retryCount = data?.retry_count ?? undefined;
          const maxRetries = data?.max_retries ?? RETRY_SCHEDULE_SECONDS.length;
          const runAt = data?.run_at_utc ?? data?.target?.run_at_utc ?? "-";
          const platform = data?.platform ?? data?.target?.platform ?? "unknown";
          const errorCode = data?.error_code ?? null;
          const errorMessage = data?.error_message ?? null;

          return (
            <article key={scheduleId} className="rounded-xl border p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-sm font-semibold text-slate-900">{scheduleId}</h2>
                <ScheduleStatusBadge status={status} retryCount={retryCount} maxRetries={maxRetries} nextRetryAt={retryAt} />
              </div>
              <p className="text-sm text-slate-700">Platform: {platform}</p>
              <p className="text-sm text-slate-700">Run at: {runAt}</p>

              {status === "failed" ? (
                <p className="mt-2 text-xs text-amber-700" title="Attempt schedule: +1m, +5m, +15m, +45m, +120m with ±20% jitter">
                  Retry schedule: +1m, +5m, +15m, +45m, +120m (±{Math.round(RETRY_JITTER_PERCENT * 100)}% jitter)
                </p>
              ) : null}

              {status === "dead_letter" ? (
                <div className="mt-2 rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700">
                  <p>Error code: {errorCode ?? "unknown"}</p>
                  <p>Error message: {errorMessage ?? "No message provided"}</p>
                </div>
              ) : null}

              {status === "awaiting_approval" ? (
                <button
                  type="button"
                  className="mt-3 rounded-lg bg-slate-900 px-3 py-2 text-xs text-white"
                  onClick={async () => {
                    try {
                      await approveSchedule(scheduleId);
                      toast.success(`Approved ${scheduleId}`);
                      query.refetch();
                    } catch {
                      toast.error("Approval failed");
                    }
                  }}
                >
                  Approve now
                </button>
              ) : null}
            </article>
          );
        })}
      </div>
    </main>
  );
}
