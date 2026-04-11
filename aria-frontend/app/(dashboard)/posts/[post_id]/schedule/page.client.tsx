// filename: app/(dashboard)/posts/[post_id]/schedule/page.client.tsx
// purpose: Scheduling page with recommended windows and manual override.

"use client";

import { useParams, useRouter } from "next/navigation";
import { useMemo } from "react";

import { PostingWindowCard } from "@/components/scheduler/PostingWindowCard";
import { PLATFORM_COOLDOWN_MINUTES } from "@/config/constants";
import { useCreateSchedule } from "@/hooks/useCreateSchedule";
import { usePostResult } from "@/hooks/usePostResult";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import { useSchedulerStore } from "@/stores/useSchedulerStore";
import type { Platform } from "@/types";

export default function PostSchedulePageClient() {
  const params = useParams<{ post_id: string }>();
  const postId = params.post_id;
  const router = useRouter();

  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
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

  const recommendations = generatedPackage?.posting_schedule_recommendation ?? [];

  const selectedCount = useMemo(() => {
    return recommendations.filter((r) => selectedWindows[r.platform]).length;
  }, [recommendations, selectedWindows]);

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
        const runAt = manualOverrides[platform] || selectedWindows[platform]?.start_local;
        if (!runAt) return null;
        return {
          platform,
          run_at_utc: runAt,
          approval_mode: approvalMode,
          status: "queued"
        };
      })
      .filter(Boolean) as Array<{ platform: Platform; run_at_utc: string; approval_mode: "human" | "auto"; status: "queued" }>;
  }, [approvalMode, manualOverrides, recommendations, selectedWindows]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Schedule post</h1>
        <p className="text-sm text-slate-600">Choose recommended windows or force a manual publish time per platform.</p>
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

      {mutation.error && (mutation.error as any).code === "HTTP_409" ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Scheduling conflict detected. Review selected windows and adjust conflicting times.
        </div>
      ) : null}

      <div className="space-y-4">
        {recommendations.map((group) => (
          <section key={group.platform} className="space-y-3 rounded-xl border p-4">
            <h2 className="text-sm font-semibold capitalize text-slate-900">{group.platform}</h2>
            <div className="grid gap-3 md:grid-cols-2">
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
              <span className="text-slate-700">Manual override ({group.platform})</span>
              <input
                type="datetime-local"
                className="w-full rounded-lg border px-3 py-2"
                onChange={(e) => {
                  const raw = e.target.value;
                  const utc = raw ? new Date(raw).toISOString() : "";
                  setManualOverride(group.platform, utc);
                }}
              />
            </label>
            {cooldownWarnings[group.platform] ? <p className="text-xs text-amber-700">{cooldownWarnings[group.platform]}</p> : null}
          </section>
        ))}
      </div>

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

      <section className="rounded-xl border p-4">
        <p className="mb-2 text-sm font-semibold text-slate-900">Schedule summary</p>
        {scheduleSummary.length === 0 ? (
          <p className="text-sm text-slate-600">No targets selected yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Platform</th>
                  <th className="px-2 py-2">Datetime UTC</th>
                  <th className="px-2 py-2">Approval mode</th>
                  <th className="px-2 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {scheduleSummary.map((row) => (
                  <tr key={`${row.platform}-${row.run_at_utc}`} className="border-b">
                    <td className="px-2 py-2 capitalize">{row.platform}</td>
                    <td className="px-2 py-2">{new Date(row.run_at_utc).toISOString()}</td>
                    <td className="px-2 py-2">{row.approval_mode}</td>
                    <td className="px-2 py-2">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <button
        type="button"
        disabled={mutation.isPending || selectedCount === 0 || Object.keys(cooldownWarnings).length > 0}
        className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        onClick={async () => {
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
            company_id: companyId,
            targets,
            approval_mode: approvalMode,
            manual_override: hasManual
              ? {
                  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                  force_window: true
                }
              : undefined
          });

          router.push("/scheduler");
        }}
      >
        {mutation.isPending ? "Submitting..." : "Create schedule"}
      </button>
    </main>
  );
}
