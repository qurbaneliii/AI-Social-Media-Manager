// filename: app/onboarding/company-profile/page.tsx
// purpose: Onboarding step for company profile capture and submission.

"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { ONBOARDING_PASS_THRESHOLD, POSTING_FREQUENCY_LIMITS } from "@/config/constants";
import { submitCompanyProfile } from "@/lib/api";
import { setClientCompanyId } from "@/lib/client-session";
import { navigateTo } from "@/lib/navigate";
import { CompanyProfileSchema } from "@/lib/zod-schemas";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { CTAType, CompanyProfileForm, Platform } from "@/types";
import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { TagInput } from "@/components/ui/TagInput";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];
const ctaTypes: CTAType[] = ["learn_more", "book_demo", "buy_now", "download", "comment", "share"];

const DEFAULT_PROFILE = {
  company_name: "Local Company",
  industry_vertical: "technology",
  target_market: {
    regions: ["US", "CA"],
    segments: ["B2B", "SMB"],
    persona_summary: "Marketing managers and founders"
  },
  tone_of_voice_descriptors: ["clear", "professional", "confident"],
  posting_frequency_goal: {
    instagram: 3,
    linkedin: 3,
    facebook: 2,
    x: 5,
    tiktok: 2,
    pinterest: 2
  },
  primary_cta_types: ["learn_more", "book_demo", "download"] as CTAType[],
  brand_color_hex_codes: ["#0EA5E9", "#0F172A", "#14B8A6"],
  approved_vocabulary_list: ["automation", "consistency", "pipeline"],
  banned_vocabulary_list: ["guaranteed", "overnight"]
};

export default function CompanyProfilePage() {
  const setCompanyId = useCompanyStore((s) => s.setCompanyId);
  const setProfile = useCompanyStore((s) => s.setProfile);

  const form = useForm<CompanyProfileForm>({
    resolver: zodResolver(CompanyProfileSchema),
    defaultValues: {
      company_name: DEFAULT_PROFILE.company_name,
      industry_vertical: DEFAULT_PROFILE.industry_vertical,
      target_market: {
        regions: [...DEFAULT_PROFILE.target_market.regions],
        segments: [...DEFAULT_PROFILE.target_market.segments],
        persona_summary: DEFAULT_PROFILE.target_market.persona_summary
      },
      brand_positioning_statement: "AI-powered social workflow automation for modern teams.",
      tone_of_voice_descriptors: [...DEFAULT_PROFILE.tone_of_voice_descriptors],
      competitor_list: [],
      platform_presence: {
        instagram: true,
        linkedin: true,
        facebook: false,
        x: true,
        tiktok: false,
        pinterest: false
      },
      posting_frequency_goal: {
        ...DEFAULT_PROFILE.posting_frequency_goal
      },
      primary_cta_types: [...DEFAULT_PROFILE.primary_cta_types],
      brand_color_hex_codes: [...DEFAULT_PROFILE.brand_color_hex_codes],
      approved_vocabulary_list: [...DEFAULT_PROFILE.approved_vocabulary_list],
      banned_vocabulary_list: [...DEFAULT_PROFILE.banned_vocabulary_list],
      logo_file: null,
      sample_post_images: []
    }
  });

  const mutation = useMutation({
    mutationFn: (payload: CompanyProfileForm) => submitCompanyProfile(payload),
    onSuccess: (data) => {
      setProfile(form.getValues());
      setCompanyId(data.company_id);
      setClientCompanyId(data.company_id);
      toast.success("Company profile saved");
      navigateTo("/onboarding/brand-assets");
    },
    onError: (error) => {
      toast.error((error as Error).message || "Failed to save company profile");
    }
  });

  const values = form.watch();

  const handleSubmit = async (payload: CompanyProfileForm) => {
    mutation.mutate(payload);
  };

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <aside className="space-y-4">
        <OnboardingProgressStepper currentStep={2} score={null} />
        <div className="rounded-xl border bg-white p-4 text-sm text-slate-600">
          Quality threshold: <span className="font-semibold text-slate-900">{ONBOARDING_PASS_THRESHOLD}</span>
        </div>
      </aside>

      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Company profile</h1>
          <p className="text-sm text-slate-600">Define strategic brand context for model grounding.</p>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Company name</span>
            <input {...form.register("company_name")} className="w-full rounded-lg border px-3 py-2" />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-slate-700">Industry vertical</span>
            <input {...form.register("industry_vertical")} className="w-full rounded-lg border px-3 py-2" />
          </label>
        </div>

        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Persona summary</span>
          <textarea {...form.register("target_market.persona_summary")} rows={3} className="w-full rounded-lg border px-3 py-2" />
        </label>

        <Controller
          control={form.control}
          name="target_market.regions"
          render={({ field }) => <TagInput label="Target regions (ISO codes)" values={field.value} onChange={field.onChange} placeholder="US, CA, GB" />}
        />

        <Controller
          control={form.control}
          name="tone_of_voice_descriptors"
          render={({ field }) => <TagInput label="Tone descriptors" values={field.value} onChange={field.onChange} />}
        />

        <Controller
          control={form.control}
          name="competitor_list"
          render={({ field }) => <TagInput label="Competitors" values={field.value} onChange={field.onChange} />}
        />

        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Brand positioning statement</span>
          <textarea {...form.register("brand_positioning_statement")} rows={4} className="w-full rounded-lg border px-3 py-2" />
        </label>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Platform presence</p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {platforms.map((platform) => (
              <label key={platform} className="flex items-center gap-2 rounded-lg border p-2 text-sm capitalize">
                <input type="checkbox" {...form.register(`platform_presence.${platform}`)} />
                {platform}
              </label>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Posting frequency goal</p>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {platforms
              .filter((platform) => values.platform_presence[platform])
              .map((platform) => (
                <label key={platform} className="space-y-1 rounded-lg border p-2 text-sm capitalize">
                  <span>{platform}</span>
                  <input
                    type="number"
                    min={0}
                    max={POSTING_FREQUENCY_LIMITS[platform]}
                    {...form.register(`posting_frequency_goal.${platform}`, { valueAsNumber: true })}
                    className="w-full rounded border px-2 py-1"
                  />
                </label>
              ))}
          </div>
          {platforms.every((platform) => !values.platform_presence[platform]) ? (
            <p className="text-xs text-amber-700">Enable at least one platform in platform presence to set posting frequency goals.</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium text-slate-700">Primary CTA types</p>
          <div className="flex flex-wrap gap-2">
            {ctaTypes.map((cta) => {
              const checked = values.primary_cta_types.includes(cta);
              return (
                <button
                  type="button"
                  key={cta}
                  onClick={() => {
                    const current = form.getValues("primary_cta_types");
                    form.setValue(
                      "primary_cta_types",
                      checked ? current.filter((v) => v !== cta) : [...current, cta],
                      { shouldValidate: true }
                    );
                  }}
                  className={`rounded-full px-3 py-1 text-xs ${checked ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
                >
                  {cta}
                </button>
              );
            })}
          </div>
        </div>

        <Controller
          control={form.control}
          name="brand_color_hex_codes"
          render={({ field }) => (
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Brand colors</label>
              <div className="flex flex-wrap items-center gap-2">
                {field.value.map((color, idx) => (
                  <div key={`${color}-${idx}`} className="flex items-center gap-2 rounded-lg border px-2 py-1">
                    <input
                      type="color"
                      value={color}
                      onChange={(e) => {
                        const next = [...field.value];
                        next[idx] = e.target.value.toUpperCase();
                        field.onChange(next);
                      }}
                      className="h-7 w-10 rounded border"
                    />
                    <span className="font-mono text-xs text-slate-600">{color.toUpperCase()}</span>
                    <button
                      type="button"
                      className="text-xs text-red-600"
                      onClick={() => field.onChange(field.value.filter((_, i) => i !== idx))}
                    >
                      Remove
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className="rounded-lg border px-2 py-1 text-xs text-slate-700"
                  onClick={() => field.onChange([...field.value, "#000000"])}
                >
                  Add color
                </button>
              </div>
            </div>
          )}
        />

        <Controller
          control={form.control}
          name="approved_vocabulary_list"
          render={({ field }) => <TagInput label="Approved vocabulary" values={field.value} onChange={field.onChange} />}
        />

        <Controller
          control={form.control}
          name="banned_vocabulary_list"
          render={({ field }) => <TagInput label="Banned vocabulary" values={field.value} onChange={field.onChange} />}
        />

        <div className="flex items-center gap-3">
          <button type="submit" disabled={mutation.isPending} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            {mutation.isPending ? "Saving..." : "Save and continue"}
          </button>
          {Object.keys(form.formState.errors).length > 0 ? <p className="text-sm text-red-600">Please resolve validation errors.</p> : null}
        </div>
      </form>
    </main>
  );
}
