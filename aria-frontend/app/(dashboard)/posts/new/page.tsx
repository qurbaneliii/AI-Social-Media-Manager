// filename: app/(dashboard)/posts/new/page.tsx
// purpose: Post generation form with RHF+Zod validation.

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";

import { FileDropzone } from "@/components/ui/FileDropzone";
import { TagInput } from "@/components/ui/TagInput";
import { useGeneratePost } from "@/hooks/useGeneratePost";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { getClientSession } from "@/lib/client-session";
import { GeneratePostSchema } from "@/lib/zod-schemas";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import type { GeneratePostForm, Platform, PostIntent } from "@/types";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];
const intents: PostIntent[] = ["announce", "educate", "promote", "engage", "inspire", "crisis_response"];

export default function NewPostPage() {
  const router = useRouter();
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const setDraftForm = usePostStore((s) => s.setDraftForm);
  const generateMutation = useGeneratePost();
  const upload = usePresignUpload();

  const form = useForm<GeneratePostForm>({
    resolver: zodResolver(GeneratePostSchema),
    defaultValues: {
      company_id: companyId ?? "",
      post_intent: "announce",
      core_message: "",
      target_platforms: ["linkedin"],
      campaign_tag: "",
      attached_media_id: undefined,
      manual_keywords: [],
      urgency_level: "immediate",
      requested_publish_at: undefined
    }
  });

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Generate post</h1>
        <p className="text-sm text-slate-600">Create intent-aligned variants, hashtags, audience definition, timing, and SEO metadata.</p>
      </header>

      <form
        className="space-y-5"
        onSubmit={form.handleSubmit(async (payload) => {
          const fullPayload = { ...payload, company_id: companyId };
          setDraftForm(fullPayload);
          const res = await generateMutation.mutateAsync(fullPayload);
          router.push(`/posts/${res.post_id}/result`);
        })}
      >
        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Post intent</span>
          <select {...form.register("post_intent")} className="w-full rounded-lg border px-3 py-2">
            {intents.map((intent) => (
              <option key={intent} value={intent}>
                {intent}
              </option>
            ))}
          </select>
        </label>

        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Core message</span>
          <textarea {...form.register("core_message")} rows={5} className="w-full rounded-lg border px-3 py-2" />
        </label>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Target platforms</p>
          <div className="flex flex-wrap gap-2">
            {platforms.map((platform) => {
              const selected = form.watch("target_platforms").includes(platform);
              return (
                <button
                  type="button"
                  key={platform}
                  onClick={() => {
                    const next = selected
                      ? form.getValues("target_platforms").filter((p) => p !== platform)
                      : [...form.getValues("target_platforms"), platform];
                    form.setValue("target_platforms", next, { shouldValidate: true });
                  }}
                  className={`rounded-full px-3 py-1 text-xs capitalize ${selected ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
                >
                  {platform}
                </button>
              );
            })}
          </div>
        </div>

        <Controller
          control={form.control}
          name="manual_keywords"
          render={({ field }) => <TagInput label="Manual keywords" values={field.value ?? []} onChange={field.onChange} />}
        />

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Campaign tag</span>
            <input {...form.register("campaign_tag")} className="w-full rounded-lg border px-3 py-2" />
          </label>

          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Urgency</span>
            <select {...form.register("urgency_level")} className="w-full rounded-lg border px-3 py-2">
              <option value="immediate">immediate</option>
              <option value="scheduled">scheduled</option>
            </select>
          </label>
        </div>

        {form.watch("urgency_level") === "scheduled" ? (
          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">Requested publish time</span>
            <input
              type="datetime-local"
              onChange={(e) => {
                const value = e.target.value ? new Date(e.target.value).toISOString() : undefined;
                form.setValue("requested_publish_at", value, { shouldValidate: true });
              }}
              className="w-full rounded-lg border px-3 py-2"
            />
          </label>
        ) : null}

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Attach media (optional)</p>
          <FileDropzone
            label="Upload media"
            onFiles={async (files) => {
              const file = files[0];
              if (!file) return;
              const assetId = await upload.upload({ company_id: companyId, file });
              form.setValue("attached_media_id", assetId, { shouldValidate: true });
            }}
            disabled={upload.isUploading}
          />
          {form.watch("attached_media_id") ? <p className="text-xs text-slate-600">Asset: {form.watch("attached_media_id")}</p> : null}
          {upload.error ? <p className="text-xs text-red-600">Upload failed. Please retry.</p> : null}
        </div>

        <button
          type="submit"
          disabled={generateMutation.isPending}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          {generateMutation.isPending ? "Generating..." : "Generate post"}
        </button>
      </form>
    </main>
  );
}
