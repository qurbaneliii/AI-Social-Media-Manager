// filename: app/onboarding/vocabulary/page.tsx
// purpose: Onboarding vocabulary curation step.

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { TagInput } from "@/components/ui/TagInput";
import { updateVocabulary } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function VocabularyPage() {
  const router = useRouter();
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;

  const [approved, setApproved] = useState<string[]>([]);
  const [banned, setBanned] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <OnboardingProgressStepper currentStep={6} score={null} />

      <section className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Vocabulary tuning</h1>
          <p className="text-sm text-slate-600">Define approved and restricted language for content safety and voice consistency.</p>
        </header>

        <TagInput label="Approved vocabulary" values={approved} onChange={setApproved} />
        <TagInput label="Banned vocabulary" values={banned} onChange={setBanned} />

        <button
          type="button"
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          disabled={isSaving}
          onClick={async () => {
            setIsSaving(true);
            try {
              await updateVocabulary(companyId, approved, banned);
              toast.success("Vocabulary saved");
              router.push("/onboarding/platforms");
            } catch (error) {
              toast.error((error as Error).message || "Failed to save vocabulary");
            } finally {
              setIsSaving(false);
            }
          }}
        >
          {isSaving ? "Saving..." : "Save and continue"}
        </button>
      </section>
    </main>
  );
}
