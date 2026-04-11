// filename: app/onboarding/quality-check/page.tsx
// purpose: Trigger and monitor onboarding quality check.

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ONBOARDING_PASS_THRESHOLD } from "@/config/constants";
import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { useQualityCheck } from "@/hooks/useQualityCheck";
import { getClientSession } from "@/lib/client-session";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function QualityCheckPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const profile = useCompanyStore((s) => s.profile);
  const remediationList = useCompanyStore((s) => s.remediationList);
  const credentials = useCompanyStore((s) => s.platformCredentials);
  const [triggeredOnMount, setTriggeredOnMount] = useState(false);

  const { status, isLoading, isError } = useOnboardingStatus(companyId);
  const qualityCheck = useQualityCheck();

  useEffect(() => {
    if (!companyId || triggeredOnMount) return;
    setTriggeredOnMount(true);
    qualityCheck.mutate(companyId);
  }, [companyId, qualityCheck, triggeredOnMount]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  const passed = (status?.score ?? 0) >= ONBOARDING_PASS_THRESHOLD && (status?.step ?? 0) >= 11;
  const activeCredentialCount = Object.values(credentials).filter((c) => c.status === "connected").length;
  const hasExpiredCredential = Object.values(credentials).some((c) => c.status === "expired");

  const checks = useMemo(() => {
    return [
      {
        label: "Brand profile completeness (positioning, tone_descriptors >= 3, confidence >= 0.6)",
        passed: Boolean(profile?.brand_positioning_statement) && (profile?.tone_of_voice_descriptors.length ?? 0) >= 3
      },
      {
        label: "Import staging (>= 10 posts)",
        passed: (status?.step ?? 0) >= 5
      },
      {
        label: "Platform credentials (>= 1 active)",
        passed: activeCredentialCount >= 1
      },
      {
        label: "Token validity (no expired tokens)",
        passed: !hasExpiredCredential
      }
    ];
  }, [activeCredentialCount, hasExpiredCredential, profile, status?.step]);

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <OnboardingProgressStepper currentStep={status?.step ?? 10} score={status?.score ?? null} />

      <section className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Quality check</h1>
          <p className="text-sm text-slate-600">Run onboarding validation and remediation before generating live content.</p>
        </header>

        <button
          type="button"
          disabled={qualityCheck.isPending}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          onClick={async () => {
            qualityCheck.mutate(companyId);
          }}
        >
          {qualityCheck.isPending ? "Starting..." : "Run quality check"}
        </button>

        <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p>Task: {qualityCheck.data?.task_id ?? "not started"}</p>
          <p>Status: {isLoading ? "loading" : isError ? "error" : status?.status ?? "idle"}</p>
          <p>Step: {status?.step ?? "-"}/11</p>
          <p>Score: {status?.score ?? "-"} (pass &gt;= {ONBOARDING_PASS_THRESHOLD})</p>
        </div>

        <div className="space-y-2 rounded-xl border p-4">
          <p className="text-sm font-semibold text-slate-900">Quality checks</p>
          {checks.map((check) => (
            <div key={check.label} className="flex items-center justify-between gap-3 rounded-lg border p-3 text-sm">
              <span className="text-slate-700">{check.label}</span>
              <span className={`rounded-full px-2 py-1 text-xs ${check.passed ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
                {check.passed ? "Pass" : "Fail"}
              </span>
            </div>
          ))}
        </div>

        {(status?.remediation ?? remediationList).length > 0 ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="mb-2 text-sm font-semibold text-amber-800">Remediation needed</p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-amber-700">
              {(status?.remediation ?? remediationList).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {passed ? (
          <Link href="/posts/new" className="inline-flex rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white">
            Start creating posts
          </Link>
        ) : (
          <p className="text-sm text-slate-600">Pass the quality threshold to unlock posting workflow.</p>
        )}
      </section>
    </main>
  );
}
