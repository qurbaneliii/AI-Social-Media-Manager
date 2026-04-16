// filename: app/(dashboard)/posts/[post_id]/schedule/page.client.tsx
// purpose: Scheduling UX with recommendation selection, timeline review, and safe submission.

"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyStateCard } from "@/components/ui/EmptyStateCard";
import { PostingWindowCard } from "@/components/scheduler/PostingWindowCard";
import { PLATFORM_COOLDOWN_MINUTES } from "@/config/constants";
import { useCreateSchedule } from "@/hooks/useCreateSchedule";
import { usePostResult } from "@/hooks/usePostResult";
import { ApiError } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { navigateTo } from "@/lib/navigate";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import { useSchedulerStore } from "@/stores/useSchedulerStore";
import type { Platform } from "@/types";

const toLocalInputValue = (isoValue: string | null) => {
  if (!isoValue) {
    return "";
  }

  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const offsetMs = date.getTimezoneOffset() * 60_000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 16);
};

export default function PostSchedulePageClient() {
  const params = useParams<{ post_id: string }>();
  const postId = params.post_id;

  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const resolvedCompanyId = companyId ?? "";
  const generatedPackage = usePostStore((s) => s.generatedPackage);
  const selectedVariantPerPlatform = usePostStore((s) => s.selectedVariantPerPlatform);

  const selectedWindows = useSchedulerStore((s) => s.selectedWindows);
  const manualOverrides = useSchedulerStore((s) => s.manualOverrides);
  const approvalMode = useSchedulerStore((s) => s.approvalMode);
  const selectWindow = useSchedulerStore((s) => s.selectWindow);
  const setManualOverride = useSchedulerStore((s) => s.setManualOverride);
  const setApprovalMode = useSchedulerStore((s) => s.setApprovalMode);
  const addTarget = useSchedulerStore((s) => s.addTarget);

  usePostResult(postId);

  const mutation = useCreateSchedule();
  const [showConfirmSubmit, setShowConfirmSubmit] = useState(false);

  const recommendations = useMemo(() => generatedPackage?.posting_schedule_recommendation ?? [], [generatedPackage]);

  const selectedCount = useMemo(() => {
    return recommendations.filter((item) => {
      const platform = item.platform as Platform;
      return Boolean(manualOverrides[platform] || selectedWindows[platform]?.start_local);
    }).length;
  }, [manualOverrides, recommendations, selectedWindows]);

  const cooldownWarnings = useMemo(() => {
    const warnings: Record<string, string> = {};
    recommendations.forEach((group) => {
      const platform = group.platform as Platform;
      const manual = manualOverrides[platform];
      const selected = selectedWindows[platform]?.start_local;
      if (!manual || !selected) return;
      const diffMinutes = Math.abs(new Date(manual).getTime() - new Date(selected).getTime()) / (60 * 1000);
      if (diffMinutes < PLATFORM_COOLDOWN_MINUTES[platform]) {
        warnings[platform] = `Manual override is within ${PLATFORM_COOLDOWN_MINUTES[platform] / 60}h cooldown window.`;
      }
    });
    return warnings;
  }, [manualOverrides, recommendations, selectedWindows]);

  const scheduleSummary = useMemo(() => {
    return recommendations
      .map((item) => {
        const platform = item.platform as Platform;
        const manual = manualOverrides[platform];
        const selected = selectedWindows[platform]?.start_local;
        const runAt = manual || selected;
        if (!runAt) return null;

        return {
          platform,
          run_at_utc: runAt,
          approval_mode: approvalMode,
          status: "queued" as const,
          source: manual ? "manual" : "recommended"
        };
      })
      .filter(Boolean)
      .sort((a, b) => new Date(a!.run_at_utc).getTime() - new Date(b!.run_at_utc).getTime()) as Array<{
      platform: Platform;
      run_at_utc: string;
      approval_mode: "human" | "auto";
      status: "queued";
      source: "manual" | "recommended";
    }>;
  }, [approvalMode, manualOverrides, recommendations, selectedWindows]);

  const canSubmit = selectedCount > 0 && Object.keys(cooldownWarnings).length === 0 && !mutation.isPending;
  const hasConflictError = mutation.error instanceof ApiError && mutation.error.code === "HTTP_409";

  const submitSchedule = async () => {
    const targets = recommendations
      .map((item) => {
        const platform = item.platform as Platform;
        const manual = manualOverrides[platform];
        const selected = selectedWindows[platform]?.start_local;
        const runAt = manual || selected;
        if (!runAt) return null;

        addTarget({ platform, run_at_utc: runAt });
        return { platform, run_at_utc: runAt };
      })
      .filter(Boolean) as { platform: Platform; run_at_utc: string }[];

    const hasManual = Object.values(manualOverrides).some(Boolean);

    await mutation.mutateAsync({
      post_id: postId,
      company_id: resolvedCompanyId,
      targets,
      approval_mode: approvalMode,
      manual_override: hasManual
        ? {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            force_window: true
          }
        : undefined
    });

    navigateTo("/scheduler");
  };

  if (!resolvedCompanyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6 aria-fade-in">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Schedule post</h1>
        <p className="text-sm text-slate-600">Select recommendation windows, optionally override times, then queue safely.</p>
      </header>

      <section className="space-y-3 rounded-xl border p-4">
        <p className="text-sm font-semibold text-slate-900">Selected variants</p>
        <div className="grid gap-2 md:grid-cols-2">
          {Object.entries(selectedVariantPerPlatform).map(([platform, variantId]) => {
            const variant = generatedPackage?.variants.find((item) => item.variant_id === variantId);
            return (
              <article key={platform} className="rounded-lg border p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{platform}</p>
                <p className="mt-1 text-xs text-slate-500">Variant: {variantId}</p>
                <p className="mt-2 line-clamp-2 text-sm text-slate-700">{variant?.text ?? "No variant selected"}</p>
              </article>
            );
          })}
        </div>
      </section>

      {hasConflictError ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Scheduling conflict detected. Review selected windows and adjust conflicting times.
        </div>
      ) : null}

      {recommendations.length === 0 ? (
        <EmptyStateCard
          title="No timing recommendations found"
          description="Generate content first to receive platform timing windows."
          actionLabel="Go to result"
          actionHref={`/posts/${postId}/result`}
        />
      ) : (
        <div className="space-y-4">
          {recommendations.map((group) => {
            const platform = group.platform as Platform;
            const manualWarning = cooldownWarnings[platform];

            return (
              <section key={group.platform} className="space-y-3 rounded-xl border p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-sm font-semibold capitalize text-slate-900">{group.platform}</h2>
                  <p className="text-xs text-slate-500">Cooldown guideline: {PLATFORM_COOLDOWN_MINUTES[platform] / 60}h</p>
                </div>

                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {group.windows.map((window) => (
                    <PostingWindowCard
                      key={`${group.platform}-${window.rank}-${window.start_local}`}
                      window={window}
                      platform={group.platform}
                      selected={selectedWindows[group.platform]?.start_local === window.start_local}
                      onSelect={() => selectWindow(group.platform, window)}
                    />
                  ))}
                </div>

                <label className="block space-y-1 text-sm">
                  <span className="font-medium text-slate-700">Manual override ({group.platform})</span>
                  {/* UX: Keep local datetime format in input while storing UTC ISO for backend compatibility. */}
                  <input
                    type="datetime-local"
                    value={toLocalInputValue(manualOverrides[platform])}
                    className="w-full rounded-lg border px-3 py-2"
                    onChange={(e) => {
                      const raw = e.target.value;
                      const utc = raw ? new Date(raw).toISOString() : "";
                      setManualOverride(group.platform, utc);
                    }}
                  />
                </label>

                {manualWarning ? <p className="text-xs text-amber-700">{manualWarning}</p> : null}
              </section>
            );
          })}
        </div>
      )}

      <section className="rounded-xl border p-4">
        <p className="mb-2 text-sm font-semibold text-slate-900">Approval mode</p>
        <div className="flex gap-2">
          {([
            { key: "auto", label: "Auto-publish" },
            { key: "human", label: "Require approval" }
          ] as const).map((mode) => (
            <button
              key={mode.key}
              type="button"
              onClick={() => setApprovalMode(mode.key)}
              className={`rounded-full px-3 py-1 text-xs ${approvalMode === mode.key ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-3 rounded-xl border p-4">
        <p className="text-sm font-semibold text-slate-900">Schedule timeline preview</p>

        {scheduleSummary.length === 0 ? (
          <p className="text-sm text-slate-600">No targets selected yet.</p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b text-left text-xs uppercase tracking-wide text-slate-500">
                    <th className="px-2 py-2">Platform</th>
                    <th className="px-2 py-2">Datetime</th>
                    <th className="px-2 py-2">Source</th>
                    <th className="px-2 py-2">Approval</th>
                  </tr>
                </thead>
                <tbody>
                  {scheduleSummary.map((row) => (
                    <tr key={`${row.platform}-${row.run_at_utc}`} className="border-b">
                      <td className="px-2 py-2 capitalize">{row.platform}</td>
                      <td className="px-2 py-2">{new Date(row.run_at_utc).toLocaleString()}</td>
                      <td className="px-2 py-2">
                        <span className={`rounded-full px-2 py-0.5 text-xs ${row.source === "manual" ? "bg-orange-100 text-orange-700" : "bg-emerald-100 text-emerald-700"}`}>
                          {row.source}
                        </span>
                      </td>
                      <td className="px-2 py-2">{row.approval_mode}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="space-y-2 rounded-xl bg-slate-50 p-3">
              {scheduleSummary.map((row) => (
                <div key={`${row.platform}-${row.run_at_utc}-timeline`} className="flex items-center gap-2 text-xs text-slate-700">
                  <span className={`inline-block h-2 w-2 rounded-full ${row.source === "manual" ? "bg-orange-500" : "bg-emerald-600"}`} />
                  <span className="font-semibold capitalize">{row.platform}</span>
                  <span>{new Date(row.run_at_utc).toLocaleString()}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <div className="flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => navigateTo(`/posts/${postId}/result`)}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
        >
          Back to result
        </button>

        <button
          type="button"
          disabled={!canSubmit}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          onClick={() => setShowConfirmSubmit(true)}
        >
          {mutation.isPending ? "Submitting..." : "Create schedule"}
        </button>
      </div>

      <ConfirmDialog
        open={showConfirmSubmit}
        title="Create schedule queue?"
        description="This will queue all selected targets with your current approval mode."
        confirmLabel="Queue schedules"
        isPending={mutation.isPending}
        onCancel={() => setShowConfirmSubmit(false)}
        onConfirm={async () => {
          await submitSchedule();
        }}
      />
    </main>
  );
}
