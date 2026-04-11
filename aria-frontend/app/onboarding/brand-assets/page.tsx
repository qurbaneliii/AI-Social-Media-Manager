// filename: app/onboarding/brand-assets/page.tsx
// purpose: Onboarding step for logo and sample media uploads.

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { getClientSession } from "@/lib/client-session";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function BrandAssetsPage() {
  const router = useRouter();
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const [logoAsset, setLogoAsset] = useState<string | null>(null);
  const [sampleAssets, setSampleAssets] = useState<string[]>([]);

  const { upload, isUploading, progress, error } = usePresignUpload();

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <OnboardingProgressStepper currentStep={5} score={null} />

      <section className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Brand assets</h1>
          <p className="text-sm text-slate-600">Upload logo and sample imagery for visual extraction and style alignment.</p>
        </header>

        <FileDropzone
          label="Upload logo"
          accept={{ "image/*": [".png", ".jpg", ".jpeg", ".svg"] }}
          onFiles={async (files) => {
            const file = files[0];
            if (!file) return;
            try {
              const assetId = await upload({ company_id: companyId, file });
              setLogoAsset(assetId);
              toast.success("Logo uploaded");
            } catch {
              toast.error("Logo upload failed. Please retry.");
            }
          }}
          disabled={isUploading}
        />

        <FileDropzone
          label="Upload sample post images"
          accept={{ "image/*": [".png", ".jpg", ".jpeg", ".webp"] }}
          multiple
          onFiles={async (files) => {
            const completed: string[] = [];
            for (const file of files) {
              try {
                const assetId = await upload({ company_id: companyId, file });
                completed.push(assetId);
              } catch {
                toast.error(`Failed to upload ${file.name}. You can retry this file.`);
              }
            }
            if (completed.length > 0) {
              setSampleAssets((prev) => [...prev, ...completed]);
              toast.success(`${completed.length} sample asset(s) uploaded`);
            }
          }}
          disabled={isUploading}
        />

        <div className="grid gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700 md:grid-cols-2">
          <p>Logo asset: {logoAsset ?? "not uploaded"}</p>
          <p>Sample assets: {sampleAssets.length}</p>
          {isUploading ? <p>Upload progress: {progress}%</p> : null}
          {error ? <p className="text-red-600">{error.message}</p> : null}
        </div>

        <button
          type="button"
          onClick={() => router.push("/onboarding/vocabulary")}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white"
        >
          Continue to vocabulary
        </button>
      </section>
    </main>
  );
}
