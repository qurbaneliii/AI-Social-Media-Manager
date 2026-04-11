// filename: app/(dashboard)/posts/[post_id]/result/page.client.tsx
// purpose: Generated post result page with review tabs and retry handling.

"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AudienceConfidenceBadge } from "@/components/audience/AudienceConfidenceBadge";
import { HashtagTierDisplay } from "@/components/hashtags/HashtagTierDisplay";
import { LLMProviderBadge } from "@/components/posts/LLMProviderBadge";
import { PlatformPreviewCard } from "@/components/posts/PlatformPreviewCard";
import { QualityScoreGauge } from "@/components/posts/QualityScoreGauge";
import { VariantScoreRadar } from "@/components/posts/VariantScoreRadar";
import { PostingWindowCard } from "@/components/scheduler/PostingWindowCard";
import { TagInput } from "@/components/ui/TagInput";
import { AUDIENCE_CONFIDENCE_THRESHOLDS, PLATFORM_CHAR_LIMITS, PLATFORM_HASHTAG_CAPS, QUALITY_SCORE_THRESHOLDS } from "@/config/constants";
import { useGeneratePost } from "@/hooks/useGeneratePost";
import { usePostResult } from "@/hooks/usePostResult";
import { usePostStore } from "@/stores/usePostStore";
import { useSchedulerStore } from "@/stores/useSchedulerStore";
import { useUIStore } from "@/stores/useUIStore";
import type { Platform } from "@/types";

const tabs = ["variants", "hashtags", "audience", "timing", "seo", "quality"] as const;

export default function PostResultPageClient() {
  const params = useParams<{ post_id: string }>();
  const postId = params.post_id;

  const draftForm = usePostStore((s) => s.draftForm);
  const generatedPackage = usePostStore((s) => s.generatedPackage);
  const generationStatus = usePostStore((s) => s.generationStatus);
  const selectedVariant = usePostStore((s) => s.selectedVariantPerPlatform);
  const selectVariant = usePostStore((s) => s.selectVariant);
  const estimate = usePostStore((s) => s.estimatedReadySeconds);
  const selectedWindows = useSchedulerStore((s) => s.selectedWindows);
  const selectWindow = useSchedulerStore((s) => s.selectWindow);

  const activeTab = useUIStore((s) => s.activePostResultTab);
  const setTab = useUIStore((s) => s.setPostResultTab);
  const activePlatformTab = useUIStore((s) => s.activePlatformTab);
  const setActivePlatform = useUIStore((s) => s.setActivePlatformTab);

  const generateMutation = useGeneratePost();
  usePostResult(postId);

  const [secondsLeft, setSecondsLeft] = useState(estimate ?? 0);
  const [seoDraft, setSeoDraft] = useState<{
    meta_title: string;
    meta_description: string;
    alt_text: string;
    keywords: string[];
  } | null>(null);

  useEffect(() => {
    setSecondsLeft(estimate ?? 0);
  }, [estimate]);

  useEffect(() => {
    if (generationStatus !== "generating") {
      return;
    }
    const id = window.setInterval(() => setSecondsLeft((s) => Math.max(0, s - 1)), 1000);
    return () => window.clearInterval(id);
  }, [generationStatus]);

  const platforms = useMemo(() => {
    return [...new Set((generatedPackage?.variants ?? []).map((v) => v.platform))] as Platform[];
  }, [generatedPackage]);

  useEffect(() => {
    if (!activePlatformTab && platforms[0]) {
      setActivePlatform(platforms[0]);
    }
  }, [activePlatformTab, platforms, setActivePlatform]);

  const variantsForPlatform = (generatedPackage?.variants ?? []).filter((v) => v.platform === activePlatformTab);
  const selected = variantsForPlatform.find((v) => v.variant_id === selectedVariant[activePlatformTab ?? ""]);
  const chosenVariant = selected ?? variantsForPlatform[0];

  useEffect(() => {
    if (!generatedPackage) return;
    setSeoDraft(generatedPackage.seo_metadata);
  }, [generatedPackage]);

  if (generationStatus === "failed") {
    return (
      <main className="space-y-4 rounded-2xl border bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Generation failed</h1>
        <p className="text-sm text-slate-600">No content package could be generated for this request.</p>
        <button
          type="button"
          disabled={generateMutation.isPending}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white"
          onClick={async () => {
            if (!draftForm.company_id) return;
            const res = await generateMutation.mutateAsync(draftForm as any);
            window.location.href = `/posts/${res.post_id}/result`;
          }}
        >
          Retry generation
        </button>
      </main>
    );
  }

  if (generationStatus === "generating" || !generatedPackage) {
    return (
      <main className="rounded-2xl border bg-white p-6">
        <h1 className="text-2xl font-semibold text-slate-900">Generating your content package</h1>
        <p className="mt-2 text-sm text-slate-600">Polling every 3 seconds. Estimated time left: {secondsLeft}s</p>
        <div className="mt-4 h-2 w-full rounded-full bg-slate-200">
          <div className="h-2 rounded-full bg-teal-600 transition-all" style={{ width: `${Math.max(5, 100 - secondsLeft)}%` }} />
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-900">Post result</h1>
        <Link href={`/posts/${postId}/schedule`} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white">
          Continue to schedule
        </Link>
      </header>

      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab}
            onClick={() => setTab(tab)}
            className={`rounded-full px-3 py-1 text-xs ${activeTab === tab ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "variants" ? (
        <section className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {platforms.map((platform) => (
              <button
                key={platform}
                type="button"
                onClick={() => setActivePlatform(platform)}
                className={`rounded-full px-3 py-1 text-xs capitalize ${activePlatformTab === platform ? "bg-teal-700 text-white" : "bg-teal-50 text-teal-700"}`}
              >
                {platform}
              </button>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
            <div className="space-y-3">
              {variantsForPlatform.slice(0, 3).map((variant) => {
                const isSelected = chosenVariant?.variant_id === variant.variant_id;
                return (
                  <button
                    key={variant.variant_id}
                    type="button"
                    className={`w-full rounded-xl border p-3 text-left ${isSelected ? "ring-2 ring-teal-600" : ""}`}
                    onClick={() => selectVariant(variant.platform, variant.variant_id)}
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs text-slate-500">{variant.variant_id}</span>
                      <div className="flex items-center gap-2">
                        <LLMProviderBadge providerUsed={variant.provider_used ?? "unknown"} cached={Boolean(variant.cached)} />
                      </div>
                    </div>
                    <p className="line-clamp-3 text-sm text-slate-800">{variant.text}</p>
                    {variant.char_count > PLATFORM_CHAR_LIMITS[variant.platform] ? (
                      <p className="mt-2 text-xs text-red-600">
                        Exceeds {variant.platform} limit by {variant.char_count - PLATFORM_CHAR_LIMITS[variant.platform]} characters.
                      </p>
                    ) : null}
                  </button>
                );
              })}
            </div>

            {chosenVariant ? <VariantScoreRadar scores={chosenVariant.scores} /> : null}
          </div>

          {chosenVariant && activePlatformTab ? (
            <PlatformPreviewCard
              platform={activePlatformTab}
              variant={chosenVariant}
              imageUrl={null}
              hashtags={[
                ...generatedPackage.hashtag_set.broad,
                ...generatedPackage.hashtag_set.niche,
                ...generatedPackage.hashtag_set.micro
              ]
                .map((item) => item.tag)
                .slice(0, 8)}
              ctaText={null}
            />
          ) : null}
        </section>
      ) : null}

      {activeTab === "hashtags" && activePlatformTab ? (
        <HashtagTierDisplay
          hashtagSet={generatedPackage.hashtag_set}
          activePlatform={activePlatformTab}
          platformCap={PLATFORM_HASHTAG_CAPS[activePlatformTab]}
        />
      ) : null}

      {activeTab === "audience" ? (
        <section className="space-y-4">
          <AudienceConfidenceBadge confidence={generatedPackage.audience_definition.confidence} />
          {generatedPackage.audience_definition.confidence < AUDIENCE_CONFIDENCE_THRESHOLDS.medium ? (
            <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
              Audience confidence is below baseline. Manual audience review is recommended.
            </p>
          ) : null}
          <p className="text-sm text-slate-700">{generatedPackage.audience_definition.natural_language_summary}</p>
        </section>
      ) : null}

      {activeTab === "timing" ? (
        <section className="space-y-3">
          {generatedPackage.posting_schedule_recommendation.map((item) => (
            <article key={item.platform} className="rounded-xl border p-3">
              <h3 className="mb-2 text-sm font-semibold capitalize text-slate-900">{item.platform}</h3>
              <div className="grid gap-3 md:grid-cols-2">
                {item.windows.slice(0, 3).map((window) => (
                  <PostingWindowCard
                    key={`${window.start_local}-${window.rank}`}
                    window={window}
                    platform={item.platform}
                    selected={selectedWindows[item.platform]?.start_local === window.start_local}
                    onSelect={() => selectWindow(item.platform, window)}
                  />
                ))}
              </div>
            </article>
          ))}
        </section>
      ) : null}

      {activeTab === "seo" ? (
        <section className="space-y-2 text-sm text-slate-700">
          <label className="block space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Title</span>
              <span className="text-xs text-slate-500">{seoDraft?.meta_title.length ?? 0}/60</span>
            </div>
            <input
              value={seoDraft?.meta_title ?? ""}
              onChange={(e) => setSeoDraft((prev) => (prev ? { ...prev, meta_title: e.target.value } : prev))}
              className="w-full rounded-lg border px-3 py-2"
            />
          </label>
          <label className="block space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Description</span>
              <span className="text-xs text-slate-500">{seoDraft?.meta_description.length ?? 0}/160</span>
            </div>
            <textarea
              value={seoDraft?.meta_description ?? ""}
              onChange={(e) => setSeoDraft((prev) => (prev ? { ...prev, meta_description: e.target.value } : prev))}
              rows={3}
              className="w-full rounded-lg border px-3 py-2"
            />
          </label>
          <label className="block space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-900">Alt text</span>
              <span className="text-xs text-slate-500">{seoDraft?.alt_text.length ?? 0}/220</span>
            </div>
            <textarea
              value={seoDraft?.alt_text ?? ""}
              onChange={(e) => setSeoDraft((prev) => (prev ? { ...prev, alt_text: e.target.value } : prev))}
              rows={2}
              className="w-full rounded-lg border px-3 py-2"
            />
          </label>
          <TagInput
            label="Keywords"
            values={seoDraft?.keywords ?? []}
            onChange={(keywords) => setSeoDraft((prev) => (prev ? { ...prev, keywords } : prev))}
          />
        </section>
      ) : null}

      {activeTab === "quality" ? (
        <section className="space-y-4">
          <QualityScoreGauge score={generatedPackage.content_quality_score} />
          {generatedPackage.content_quality_score.overall < QUALITY_SCORE_THRESHOLDS.warning ? (
            <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">Overall quality is low. Revise prompt and regenerate.</p>
          ) : generatedPackage.content_quality_score.overall < QUALITY_SCORE_THRESHOLDS.good ? (
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">Quality is acceptable but can be improved before publishing.</p>
          ) : (
            <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">Quality score is strong for publishing.</p>
          )}
        </section>
      ) : null}
    </main>
  );
}
