// filename: app/onboarding/quality-check/page.tsx
// purpose: Trigger and monitor onboarding quality check.

"use client";

import Link from "next/link";
import { useState } from "react";

import { ONBOARDING_PASS_THRESHOLD } from "@/config/constants";
import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { triggerQualityCheck } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function QualityCheckPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);

  const { status, isLoading, isError } = useOnboardingStatus(companyId);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  const passed = (status?.score ?? 0) >= ONBOARDING_PASS_THRESHOLD && (status?.step ?? 0) >= 11;

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
          disabled={isTriggering}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          onClick={async () => {
            setIsTriggering(true);
            try {
              const result = await triggerQualityCheck(companyId);
              setTaskId(result.task_id);
            } finally {
              setIsTriggering(false);
            }
          }}
        >
          {isTriggering ? "Starting..." : "Run quality check"}
        </button>

        <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
          <p>Task: {taskId ?? "not started"}</p>
          <p>Status: {isLoading ? "loading" : isError ? "error" : status?.status ?? "idle"}</p>
          <p>Step: {status?.step ?? "-"}/11</p>
          <p>Score: {status?.score ?? "-"} (pass &gt;= {ONBOARDING_PASS_THRESHOLD})</p>
        </div>

        {status?.remediation && status.remediation.length > 0 ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="mb-2 text-sm font-semibold text-amber-800">Remediation needed</p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-amber-700">
              {status.remediation.map((item) => (
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
