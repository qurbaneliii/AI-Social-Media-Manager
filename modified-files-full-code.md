## .github/workflows/deploy.yml
~~~
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: aria-frontend/package-lock.json

      - name: Install dependencies
        working-directory: aria-frontend
        run: npm ci

      - name: Build
        working-directory: aria-frontend
        run: npm run build
        env:
          NEXT_PUBLIC_IS_STATIC: true
          NEXT_PUBLIC_BASE_PATH: /AI-Social-Media-Manager
          OPENAI_API_KEY: dummy

      - name: Add .nojekyll
        working-directory: aria-frontend
        run: touch out/.nojekyll

      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./aria-frontend/out

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4

~~~

## aria-frontend/app/(auth)/signin/page.tsx
~~~
"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function LegacySignInPage() {
  useEffect(() => {
    navigateTo("/login");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Redirecting...</main>;
}

~~~

## aria-frontend/app/(dashboard)/layout.tsx
~~~
// filename: app/(dashboard)/layout.tsx
// purpose: Dashboard shell with role-aware navigation and route guards.

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo } from "react";
import { BarChart3, CalendarClock, FileText, LogOut, PlusCircle } from "lucide-react";

import { useAuth } from "@/context/AuthContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { navigateTo } from "@/lib/navigate";
import type { UserRole } from "@/types";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
}

const roleNav: Record<UserRole, NavItem[]> = {
  agency_admin: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ],
  brand_manager: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ],
  content_creator: [
    { href: "/posts/new", label: "Create Post", icon: <PlusCircle className="h-4 w-4" /> },
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/scheduler", label: "Scheduler", icon: <CalendarClock className="h-4 w-4" /> }
  ],
  analyst: [
    { href: "/posts", label: "Posts", icon: <FileText className="h-4 w-4" /> },
    { href: "/analytics", label: "Analytics", icon: <BarChart3 className="h-4 w-4" /> }
  ]
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { isLoading } = useRequireAuth();

  const activeRole = user?.role ?? null;

  const navItems = useMemo(() => {
    if (!activeRole) {
      return [];
    }
    return roleNav[activeRole];
  }, [activeRole]);

  useEffect(() => {
    if (isLoading || !activeRole) {
      return;
    }
    const allowed = roleNav[activeRole].some((item) => pathname.startsWith(item.href));
    if (!allowed) {
      const fallback = roleNav[activeRole][0]?.href ?? "/posts";
      navigateTo(fallback);
    }
  }, [activeRole, isLoading, pathname]);

  if (isLoading) {
    return <div className="min-h-screen bg-slate-50 px-4 py-8 text-sm text-slate-600">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-500">ARIA</p>
            <p className="text-sm font-semibold text-slate-800">Role: {activeRole ?? "loading"}</p>
          </div>
          <button
            type="button"
            onClick={logout}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-xs text-slate-700"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 md:grid-cols-[220px_1fr]">
        <aside className="rounded-xl border border-slate-200 bg-white p-3">
          <nav className="space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  pathname.startsWith(item.href) ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
                }`}
              >
                {item.icon}
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <main>{children}</main>
      </div>
    </div>
  );
}

~~~

## aria-frontend/app/(dashboard)/posts/[post_id]/result/page.client.tsx
~~~
// filename: app/(dashboard)/posts/[post_id]/result/page.client.tsx
// purpose: Generated post result page with review tabs and retry handling.

"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

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
import { navigateTo } from "@/lib/navigate";
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
            navigateTo(`/posts/${res.post_id}/result`);
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
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={!chosenVariant?.text}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-60"
            onClick={async () => {
              if (!chosenVariant?.text) {
                return;
              }
              try {
                await navigator.clipboard.writeText(chosenVariant.text);
                toast.success("Copied generated content");
              } catch {
                toast.error("Could not copy content");
              }
            }}
          >
            Copy selected content
          </button>

          <button
            type="button"
            disabled={generateMutation.isPending || !draftForm.company_id}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-60"
            onClick={async () => {
              if (!draftForm.company_id) {
                toast.error("Missing draft payload for regeneration");
                return;
              }

              const regenerated = await generateMutation.mutateAsync(draftForm as any);
              navigateTo(`/posts/${regenerated.post_id}/result`);
            }}
          >
            {generateMutation.isPending ? "Regenerating..." : "Regenerate"}
          </button>

          <Link href={`/posts/${postId}/schedule`} className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white">
            Continue to schedule
          </Link>
        </div>
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

~~~

## aria-frontend/app/(dashboard)/posts/[post_id]/schedule/page.client.tsx
~~~
// filename: app/(dashboard)/posts/[post_id]/schedule/page.client.tsx
// purpose: Scheduling page with recommended windows and manual override.

"use client";

import { useParams } from "next/navigation";
import { useMemo } from "react";

import { PostingWindowCard } from "@/components/scheduler/PostingWindowCard";
import { PLATFORM_COOLDOWN_MINUTES } from "@/config/constants";
import { useCreateSchedule } from "@/hooks/useCreateSchedule";
import { usePostResult } from "@/hooks/usePostResult";
import { getClientSession } from "@/lib/client-session";
import { navigateTo } from "@/lib/navigate";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import { useSchedulerStore } from "@/stores/useSchedulerStore";
import type { Platform } from "@/types";

export default function PostSchedulePageClient() {
  const params = useParams<{ post_id: string }>();
  const postId = params.post_id;

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

          navigateTo("/scheduler");
        }}
      >
        {mutation.isPending ? "Submitting..." : "Create schedule"}
      </button>
    </main>
  );
}

~~~

## aria-frontend/app/(dashboard)/posts/new/page.tsx
~~~
// filename: app/(dashboard)/posts/new/page.tsx
// purpose: Post generation form with RHF+Zod validation.

"use client";

import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { FileDropzone } from "@/components/ui/FileDropzone";
import { PLATFORM_CHAR_LIMITS } from "@/config/constants";
import { TagInput } from "@/components/ui/TagInput";
import { useAuth } from "@/context/AuthContext";
import { useGeneratePost } from "@/hooks/useGeneratePost";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { getClientSession } from "@/lib/client-session";
import { IS_STATIC } from "@/lib/isStatic";
import { navigateTo } from "@/lib/navigate";
import { mockCompanyProfile } from "@/lib/mockData";
import { GeneratePostSchema } from "@/lib/zod-schemas";
import {
  analyzeContent,
  generateBatch,
  generateContent,
  improveContent,
  suggestHashtags,
  suggestTopics,
  type AIAnalyzeContentResponse,
  type AIGenerateBatchResult,
  type AIPlatform
} from "@/services/aiService";
import { useCompanyStore } from "@/stores/useCompanyStore";
import { usePostStore } from "@/stores/usePostStore";
import type { GeneratePostForm, Platform, PostIntent, UserRole } from "@/types";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];
const intents: PostIntent[] = ["announce", "educate", "promote", "engage", "inspire", "crisis_response"];

const roleDefaultIntent: Record<UserRole, PostIntent> = {
  agency_admin: "promote",
  brand_manager: "announce",
  content_creator: "engage",
  analyst: "educate"
};

const toAIPlatform = (platform: Platform): AIPlatform => {
  return platform === "x" ? "twitter" : platform;
};

const toPlatform = (platform: AIPlatform): Platform => {
  return platform === "twitter" ? "x" : platform;
};

const getFriendlyAiError = (error: unknown): string => {
  if (!(error instanceof Error)) {
    return "Failed to generate content. Please try again.";
  }

  const message = error.message.toLowerCase();
  if (message.includes("quota") || message.includes("rate") || message.includes("temporarily") || message.includes("503")) {
    return "OpenAI service is temporarily unavailable.";
  }

  return "Failed to generate content. Please try again.";
};

export default function NewPostPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const profile = useCompanyStore((s) => s.profile);
  const { user } = useAuth();
  const setDraftForm = usePostStore((s) => s.setDraftForm);
  const generateMutation = useGeneratePost();
  const upload = usePresignUpload();

  const [didPrefillFromProfile, setDidPrefillFromProfile] = useState(false);
  const [aiPlatform, setAiPlatform] = useState<AIPlatform>("linkedin");
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [isBatchGenerating, setIsBatchGenerating] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSuggestingHashtags, setIsSuggestingHashtags] = useState(false);
  const [isSuggestingTopics, setIsSuggestingTopics] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState("");
  const [improvedContent, setImprovedContent] = useState("");
  const [improveInstruction, setImproveInstruction] = useState("Make it sharper and more action-oriented.");
  const [analysis, setAnalysis] = useState<AIAnalyzeContentResponse | null>(null);
  const [hashtags, setHashtags] = useState<string[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [batchResults, setBatchResults] = useState<AIGenerateBatchResult[]>([]);

  const resolvedCompanyProfile = profile
    ? {
        platforms: platforms.filter((platform) => profile.platform_presence[platform]).map(toAIPlatform),
        postingFrequency: profile.posting_frequency_goal,
        ctaTypes: profile.primary_cta_types,
        brandColors: profile.brand_color_hex_codes,
        approvedVocabulary: profile.approved_vocabulary_list,
        bannedVocabulary: profile.banned_vocabulary_list,
        companyName: profile.company_name,
        industry: profile.industry_vertical,
        targetMarket: profile.target_market,
        tone: profile.tone_of_voice_descriptors
      }
    : IS_STATIC
      ? mockCompanyProfile
      : null;

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

  useEffect(() => {
    if ((!profile && !IS_STATIC) || didPrefillFromProfile) {
      return;
    }

    const activePlatforms = profile
      ? platforms.filter((platform) => profile.platform_presence[platform])
      : mockCompanyProfile.platforms.map((platform) => (platform === "twitter" ? "x" : platform as Platform));
    if (activePlatforms.length > 0) {
      form.setValue("target_platforms", activePlatforms, { shouldValidate: true });
      setAiPlatform(toAIPlatform(activePlatforms[0]));
    }

    const approved = profile?.approved_vocabulary_list ?? [...mockCompanyProfile.approvedVocabulary];
    if (approved.length > 0) {
      form.setValue("manual_keywords", approved.slice(0, 8), { shouldValidate: true });
    }

    if (user?.role) {
      form.setValue("post_intent", roleDefaultIntent[user.role], { shouldValidate: true });
    }

    setDidPrefillFromProfile(true);
  }, [didPrefillFromProfile, form, profile, user?.role]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  const selectedTargets = form.watch("target_platforms");
  const strictestLimit = selectedTargets.length
    ? Math.min(...selectedTargets.map((platform) => PLATFORM_CHAR_LIMITS[platform]))
    : 0;
  const coreMessageLength = form.watch("core_message").length;
  const aiResult = improvedContent || generatedContent;

  const buildGeneratePayload = (platformOverride?: AIPlatform) => {
    if (!resolvedCompanyProfile) {
      return null;
    }

    const resolvedPlatform = platformOverride ?? aiPlatform;
    const frontendPlatform = toPlatform(resolvedPlatform);
    const topic =
      form.getValues("core_message").trim() || `${profile?.company_name ?? "Preview Company"} update`;

    return {
      platform: resolvedPlatform,
      topic,
      tone: profile ? profile.tone_of_voice_descriptors.join(", ") || "professional" : "professional",
      ctaType: (profile?.primary_cta_types[0] ?? mockCompanyProfile.ctaTypes[0]) as any,
      brandColors: profile?.brand_color_hex_codes ?? [...mockCompanyProfile.brandColors],
      approvedVocabulary: profile?.approved_vocabulary_list ?? [...mockCompanyProfile.approvedVocabulary],
      bannedVocabulary: profile?.banned_vocabulary_list ?? [...mockCompanyProfile.bannedVocabulary],
      postingFrequency: profile
        ? profile.posting_frequency_goal[frontendPlatform]
        : mockCompanyProfile.postingFrequency[frontendPlatform === "x" ? "twitter" : "linkedin"],
      companyProfile: {
        companyId,
        ...resolvedCompanyProfile,
        selectedPlatforms: selectedTargets,
        userRole: user?.role ?? null
      }
    };
  };

  const handleGenerateWithAI = async () => {
    const payload = buildGeneratePayload();
    if (!payload) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    setAiError(null);
    setIsGeneratingAI(true);
    try {
      const response = await generateContent(payload);
      setGeneratedContent(response.content);
      setImprovedContent("");
      setAnalysis(null);
      setHashtags([]);
      toast.success("AI content generated");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const handleBatchGenerate = async () => {
    if (!resolvedCompanyProfile) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    const targetPlatforms = selectedTargets.length > 0 ? selectedTargets : [toPlatform(aiPlatform)];
    const payloads = targetPlatforms
      .map((platform) => buildGeneratePayload(toAIPlatform(platform)))
      .filter((item): item is NonNullable<typeof item> => item !== null);

    if (!payloads.length) {
      setAiError("Select at least one platform to generate batch content");
      return;
    }

    setAiError(null);
    setIsBatchGenerating(true);
    try {
      const response = await generateBatch(payloads);
      setBatchResults(response.results);

      const firstSuccess = response.results.find((item) => item.success && item.content);
      if (firstSuccess?.content) {
        setGeneratedContent(firstSuccess.content);
        setImprovedContent("");
        setAiPlatform(firstSuccess.platform);
      }
      toast.success("Batch generation completed");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsBatchGenerating(false);
    }
  };

  const handleImproveContent = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before improving it");
      return;
    }

    setAiError(null);
    setIsImproving(true);
    try {
      const response = await improveContent({ content: aiResult, instruction: improveInstruction });
      setImprovedContent(response.improved);
      toast.success("Content improved");
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsImproving(false);
    }
  };

  const handleAnalyzeContent = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before analyzing it");
      return;
    }

    setAiError(null);
    setIsAnalyzing(true);
    try {
      const response = await analyzeContent({ content: aiResult, platform: aiPlatform });
      setAnalysis(response);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSuggestHashtags = async () => {
    if (!aiResult.trim()) {
      setAiError("Generate content first before suggesting hashtags");
      return;
    }

    setAiError(null);
    setIsSuggestingHashtags(true);
    try {
      const response = await suggestHashtags({ content: aiResult, platform: aiPlatform });
      setHashtags(response.hashtags);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsSuggestingHashtags(false);
    }
  };

  const handleSuggestTopics = async () => {
    if (!resolvedCompanyProfile) {
      setAiError("Complete your company profile for better AI results");
      return;
    }

    const platformsForTopicRequest =
      selectedTargets.length > 0 ? selectedTargets.map(toAIPlatform) : [aiPlatform];

    setAiError(null);
    setIsSuggestingTopics(true);
    try {
      const response = await suggestTopics({
        industry: profile?.industry_vertical ?? "marketing",
        platforms: platformsForTopicRequest,
        companyProfile: {
          companyId,
          companyName: profile?.company_name ?? "Preview Company",
          userRole: user?.role ?? null,
          targetMarket: profile?.target_market ?? {},
          tone: profile?.tone_of_voice_descriptors ?? ["professional"]
        }
      });
      setTopics(response.topics);
    } catch (error) {
      setAiError(getFriendlyAiError(error));
    } finally {
      setIsSuggestingTopics(false);
    }
  };

  const copyResultToClipboard = async () => {
    if (!aiResult.trim()) {
      return;
    }

    try {
      await navigator.clipboard.writeText(aiResult);
      toast.success("Generated content copied");
    } catch {
      toast.error("Could not copy content");
    }
  };

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
          navigateTo(`/posts/${res.post_id}/result`);
        })}
      >
        <label className="block space-y-1 text-sm">
          <span className="text-slate-700">Post intent</span>
          <div className="flex flex-wrap gap-2">
            {intents.map((intent) => (
              <button
                key={intent}
                type="button"
                onClick={() => form.setValue("post_intent", intent, { shouldValidate: true })}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("post_intent") === intent ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                {intent}
              </button>
            ))}
          </div>
        </label>

        <label className="block space-y-1 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-slate-700">Core message</span>
            <span className={`text-xs ${strictestLimit > 0 && coreMessageLength > strictestLimit ? "text-red-600" : "text-slate-500"}`}>
              {coreMessageLength}/{strictestLimit || 500}
            </span>
          </div>
          <textarea {...form.register("core_message")} rows={5} className="w-full rounded-lg border px-3 py-2" />
          {strictestLimit > 0 && coreMessageLength > strictestLimit ? (
            <p className="text-xs text-red-600">Core message exceeds strictest selected platform limit by {coreMessageLength - strictestLimit} characters.</p>
          ) : null}
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
                  {platform} ({PLATFORM_CHAR_LIMITS[platform]})
                </button>
              );
            })}
          </div>
        </div>

        <section className="space-y-4 rounded-xl border border-teal-200 bg-teal-50/50 p-4">
          <header className="space-y-1">
            <h2 className="text-sm font-semibold text-teal-900">AI Content Studio</h2>
            <p className="text-xs text-teal-800">
              Generate, improve, analyze, and optimize copy using your company profile constraints.
            </p>
          </header>

          {!resolvedCompanyProfile ? (
            <p className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Complete your company profile for better AI results. {" "}
              <Link href="/onboarding/company-profile" className="font-medium underline">
                Go to company profile settings
              </Link>
            </p>
          ) : IS_STATIC ? (
            <p className="rounded-lg border border-sky-300 bg-sky-50 px-3 py-2 text-xs text-sky-800">
              Preview mode: AI actions are using mock/static responses.
            </p>
          ) : null}

          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">AI platform</span>
            <select
              value={aiPlatform}
              onChange={(event) => setAiPlatform(event.target.value as AIPlatform)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              {platforms.map((platform) => {
                const value = toAIPlatform(platform);
                return (
                  <option key={platform} value={value}>
                    {platform}
                  </option>
                );
              })}
            </select>
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleGenerateWithAI}
              disabled={isGeneratingAI}
              className="rounded-lg bg-teal-700 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {isGeneratingAI ? "Generating..." : "Create with AI"}
            </button>

            <button
              type="button"
              onClick={handleBatchGenerate}
              disabled={isBatchGenerating}
              className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {isBatchGenerating ? "Generating batch..." : "Generate batch"}
            </button>

            <button
              type="button"
              onClick={handleGenerateWithAI}
              disabled={isGeneratingAI || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              Regenerate
            </button>
          </div>

          {aiError ? <p className="text-xs text-red-700">{aiError}</p> : null}

          {aiResult ? (
            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-700">Generated content</label>
              <textarea
                readOnly
                value={aiResult}
                rows={6}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={copyResultToClipboard}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700"
                >
                  Copy
                </button>
                <button
                  type="button"
                  onClick={() => form.setValue("core_message", aiResult.slice(0, 500), { shouldValidate: true })}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700"
                >
                  Use as core message
                </button>
              </div>
            </div>
          ) : null}

          <label className="block space-y-1 text-sm">
            <span className="text-slate-700">Improve instruction</span>
            <input
              value={improveInstruction}
              onChange={(event) => setImproveInstruction(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Example: Make this more concise and high-converting"
            />
          </label>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleImproveContent}
              disabled={isImproving || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isImproving ? "Improving..." : "Improve content"}
            </button>

            <button
              type="button"
              onClick={handleAnalyzeContent}
              disabled={isAnalyzing || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isAnalyzing ? "Analyzing..." : "Analyze content"}
            </button>

            <button
              type="button"
              onClick={handleSuggestHashtags}
              disabled={isSuggestingHashtags || !aiResult}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isSuggestingHashtags ? "Suggesting..." : "Suggest hashtags"}
            </button>

            <button
              type="button"
              onClick={handleSuggestTopics}
              disabled={isSuggestingTopics}
              className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 disabled:opacity-60"
            >
              {isSuggestingTopics ? "Suggesting..." : "Suggest topics"}
            </button>
          </div>

          {analysis ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="font-semibold text-slate-900">Quality analysis</p>
              <p>Engagement: {analysis.scores.engagement}</p>
              <p>Clarity: {analysis.scores.clarity}</p>
              <p>CTA strength: {analysis.scores.cta_strength}</p>
              <ul className="mt-2 list-disc pl-5">
                {analysis.suggestions.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {hashtags.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Suggested hashtags</p>
              <div className="flex flex-wrap gap-2">
                {hashtags.map((tag) => (
                  <span key={tag} className="rounded-full bg-slate-100 px-2 py-1">
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {topics.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Suggested topics</p>
              <ul className="list-disc pl-5">
                {topics.map((topic) => (
                  <li key={topic}>{topic}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {batchResults.length > 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-700">
              <p className="mb-2 font-semibold text-slate-900">Batch generation results</p>
              <ul className="space-y-1">
                {batchResults.map((result, index) => (
                  <li key={`${result.platform}-${index}`}>
                    <span className="font-medium capitalize">{result.platform}:</span>{" "}
                    {result.success ? "Success" : result.error ?? "Failed"}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

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
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  form.setValue("urgency_level", "scheduled", { shouldValidate: true });
                }}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("urgency_level") === "scheduled" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                Schedule later
              </button>
              <button
                type="button"
                onClick={() => {
                  form.setValue("urgency_level", "immediate", { shouldValidate: true });
                  form.setValue("requested_publish_at", undefined, { shouldValidate: true });
                }}
                className={`rounded-full px-3 py-1 text-xs ${form.watch("urgency_level") === "immediate" ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"}`}
              >
                Publish now
              </button>
            </div>
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

~~~

## aria-frontend/app/api/auth/login/route.ts
~~~
import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { z } from "zod";

import { signAuthToken } from "@/lib/auth";
import { AUTH_COOKIE_NAME, AUTH_TOKEN_EXPIRY_SECONDS } from "@/lib/auth-constants";
import { prisma } from "@/lib/prisma";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

const loginSchema = z.object({
  email: z.string().trim().email(),
  password: z.string().min(8)
});

export async function POST(request: Request) {
  if (isStatic) {
    return NextResponse.json({ error: "Authentication requires a live server." }, { status: 503 });
  }

  try {
    const payload = loginSchema.parse(await request.json());

    const user = await prisma.user.findUnique({
      where: { email: payload.email }
    });

    if (!user) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const isValidPassword = await bcrypt.compare(payload.password, user.password);
    if (!isValidPassword) {
      return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
    }

    const token = signAuthToken({ userId: user.id, email: user.email, role: user.role });

    const response = NextResponse.json(
      {
        token,
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          role: user.role
        }
      },
      { status: 200 }
    );

    response.cookies.set({
      name: AUTH_COOKIE_NAME,
      value: token,
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: AUTH_TOKEN_EXPIRY_SECONDS,
      path: "/"
    });

    return response;
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: "Invalid input",
          details: error.flatten()
        },
        { status: 400 }
      );
    }

    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

~~~

## aria-frontend/app/api/auth/logout/route.ts
~~~
import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth-constants";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

export async function POST() {
  if (isStatic) {
    return NextResponse.json({ message: "Preview mode" }, { status: 200 });
  }

  const response = NextResponse.json({ message: "Logged out" }, { status: 200 });
  response.cookies.set({
    name: AUTH_COOKIE_NAME,
    value: "",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0,
    path: "/"
  });
  return response;
}

~~~

## aria-frontend/app/api/auth/me/route.ts
~~~
import { NextRequest, NextResponse } from "next/server";

import { verifyAuthToken } from "@/lib/auth";
import { AUTH_COOKIE_NAME } from "@/lib/auth-constants";
import { prisma } from "@/lib/prisma";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

export async function GET(request: NextRequest) {
  if (isStatic) {
    return NextResponse.json({ error: "Authentication requires a live server." }, { status: 401 });
  }

  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
    if (!token) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const payload = verifyAuthToken(token);
    if (!payload) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const user = await prisma.user.findUnique({
      where: { id: payload.userId },
      select: {
        id: true,
        email: true,
        name: true,
        role: true
      }
    });

    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    return NextResponse.json({ user }, { status: 200 });
  } catch {
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

~~~

## aria-frontend/app/api/auth/register/route.ts
~~~
import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { z } from "zod";

import { prisma } from "@/lib/prisma";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

const roleSchema = z.enum(["agency_admin", "brand_manager", "content_creator", "analyst"]);

const registerSchema = z.object({
  name: z.string().trim().min(1).max(120),
  email: z.string().trim().email(),
  password: z.string().min(8),
  role: roleSchema
});

export async function POST(request: Request) {
  if (isStatic) {
    return NextResponse.json({ error: "Authentication requires a live server." }, { status: 503 });
  }

  try {
    const payload = registerSchema.parse(await request.json());
    const existing = await prisma.user.findUnique({ where: { email: payload.email } });

    if (existing) {
      return NextResponse.json({ error: "Email already exists" }, { status: 409 });
    }

    const hashedPassword = await bcrypt.hash(payload.password, 12);

    const user = await prisma.user.create({
      data: {
        name: payload.name,
        email: payload.email,
        password: hashedPassword,
        role: payload.role
      },
      select: {
        id: true,
        email: true,
        role: true
      }
    });

    return NextResponse.json(
      {
        message: "User created",
        user
      },
      { status: 201 }
    );
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: "Invalid input",
          details: error.flatten()
        },
        { status: 400 }
      );
    }

    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

~~~

## aria-frontend/app/dashboard/page.tsx
~~~
"use client";

import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { useRequireAuth } from "@/hooks/useRequireAuth";
import { navigateTo } from "@/lib/navigate";
import { getRoleRedirectPath } from "@/lib/role-routing";

export default function DashboardPage() {
  const { isLoading } = useRequireAuth();
  const { user } = useAuth();

  useEffect(() => {
    if (!isLoading && user) {
      navigateTo(getRoleRedirectPath(user.role));
    }
  }, [isLoading, user]);

  if (isLoading) {
    return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Loading...</main>;
  }

  return (
    <main className="mx-auto max-w-4xl space-y-4 px-4 py-10">
      <h1 className="text-3xl font-semibold text-slate-900">Dashboard</h1>
      <p className="text-slate-600">Redirecting...</p>
    </main>
  );
}

~~~

## aria-frontend/app/login/page.tsx
~~~
"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AUTH_PREVIEW_MESSAGE } from "@/lib/mockData";
import { getBasePath } from "@/lib/navigate";
import type { UserRole } from "@/types";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreviewModeNotice, setShowPreviewModeNotice] = useState(false);

  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const params = new URLSearchParams(window.location.search);
    setRegistered(params.get("registered") === "1");
  }, []);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setShowPreviewModeNotice(false);

    if (email === "preview@ariaconsole.com" &&
        password === "Preview123!") {
      localStorage.setItem("user", JSON.stringify({
        id: "preview-user-001",
        name: "Preview User",
        email: "preview@ariaconsole.com",
        role: "brand_manager"
      }));
      localStorage.setItem("token", "preview-token-static-mode");
      localStorage.setItem("isPreview", "true");
      window.location.href = "/AI-Social-Media-Manager/dashboard";
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email: email.trim(), password })
      });

      let data: { token?: string; user?: { role?: UserRole }; error?: string } = {};
      try {
        data = (await response.json()) as { token?: string; user?: { role?: UserRole }; error?: string };
      } catch {
        data = {};
      }

      if (!response.ok) {
        setError(data.error ?? "Invalid email or password");
        return;
      }

      if (!data.token || !data.user?.role) {
        setError("Invalid server response.");
        return;
      }

      if (typeof window !== "undefined") {
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        localStorage.setItem("aria_token", data.token);
        sessionStorage.setItem("aria_token", data.token);
        localStorage.setItem("aria_role", data.user.role);
      }

      const role = data.user.role;
      if (role === "agency_admin") {
        window.location.href = `${getBasePath()}/dashboard/admin`;
      } else if (role === "brand_manager") {
        window.location.href = `${getBasePath()}/dashboard/brand`;
      } else if (role === "content_creator") {
        window.location.href = `${getBasePath()}/dashboard/content`;
      } else if (role === "analyst") {
        window.location.href = `${getBasePath()}/dashboard/analytics`;
      } else {
        window.location.href = `${getBasePath()}/dashboard`;
      }
    } catch {
      setError("Connection failed. Please try again.");
      setShowPreviewModeNotice(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePreviewLogin = () => {
    const previewUser = {
      id: "preview-user-001",
      name: "Preview User",
      email: "preview@ariaconsole.com",
      role: "brand_manager"
    };
    localStorage.setItem("user", JSON.stringify(previewUser));
    localStorage.setItem("token", "preview-token-static-mode");
    localStorage.setItem("isPreview", "true");
    window.location.href = "/AI-Social-Media-Manager/dashboard";
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center px-4 py-8">
      <section className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl md:grid-cols-2">
        <div className="bg-gradient-to-br from-teal-700 via-sky-700 to-cyan-700 p-8 text-white">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">ARIA Console</p>
          <h1 className="mt-3 text-3xl font-semibold">Scale your social pipeline</h1>
          <p className="mt-4 text-sm text-cyan-100">Generate platform-native content, review quality signals, and schedule with confidence.</p>
        </div>

        <form onSubmit={submit} className="space-y-4 p-8">
          <h2 className="text-xl font-semibold text-slate-900">Sign in</h2>

          {registered ? <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">Account created. Please sign in.</p> : null}

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Email</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Password</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error ? <p className="text-xs text-red-600">{error}</p> : null}

          {showPreviewModeNotice ? <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">{AUTH_PREVIEW_MESSAGE}</p> : null}

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>

          <button
            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700"
            type="button"
            onClick={handlePreviewLogin}
          >
            Continue as Preview User
          </button>

          <p className="text-sm text-slate-600">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-slate-900 underline">
              Register
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}

~~~

## aria-frontend/app/oauth/callback/page.tsx
~~~
// filename: app/oauth/callback/page.tsx
// purpose: OAuth callback relay that forwards callback params to onboarding platform connection screen.

"use client";

import { useEffect } from "react";
import { getBasePath } from "@/lib/navigate";

export default function OAuthCallbackPage() {
  useEffect(() => {
    const query = window.location.search.replace(/^\?/, "");
    const next = query ? `/onboarding/platforms?${query}` : "/onboarding/platforms";
    window.location.replace(`${getBasePath()}${next}`);
  }, []);

  return (
    <main className="rounded-xl border bg-white p-6 text-sm text-slate-700">
      Processing OAuth callback...
    </main>
  );
}

~~~

## aria-frontend/app/onboarding/brand-assets/page.tsx
~~~
// filename: app/onboarding/brand-assets/page.tsx
// purpose: Onboarding step for logo and sample media uploads.

"use client";

import { useState } from "react";
import { toast } from "sonner";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { FileDropzone } from "@/components/ui/FileDropzone";
import { importPostArchive } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { usePresignUpload } from "@/hooks/usePresignUpload";
import { navigateTo } from "@/lib/navigate";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function BrandAssetsPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const [logoAsset, setLogoAsset] = useState<string | null>(null);
  const [sampleAssets, setSampleAssets] = useState<string[]>([]);
  const [importStagedCount, setImportStagedCount] = useState<number | null>(null);
  const [importSkippedCount, setImportSkippedCount] = useState<number | null>(null);
  const [importingArchive, setImportingArchive] = useState(false);
  const [progressByFile, setProgressByFile] = useState<Record<string, number>>({});

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
              const assetId = await upload({
                company_id: companyId,
                file,
                onProgress: (pct) => {
                  setProgressByFile((prev) => ({ ...prev, [file.name]: pct }));
                }
              });
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
                const assetId = await upload({
                  company_id: companyId,
                  file,
                  onProgress: (pct) => {
                    setProgressByFile((prev) => ({ ...prev, [file.name]: pct }));
                  }
                });
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

        <FileDropzone
          label="Upload post archive (.csv or .json)"
          accept={{
            "text/csv": [".csv"],
            "application/json": [".json"]
          }}
          onFiles={async (files) => {
            const file = files[0];
            if (!file) return;
            setImportingArchive(true);
            try {
              const result = await importPostArchive(companyId, file);
              setImportStagedCount(result.staged_count);
              setImportSkippedCount(result.skipped_count);
              toast.success(`Archive imported. Staged ${result.staged_count} posts.`);
            } catch (e) {
              toast.error((e as Error).message || "Post archive import failed");
            } finally {
              setImportingArchive(false);
            }
          }}
          disabled={importingArchive}
        />

        <div className="grid gap-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-700 md:grid-cols-2">
          <p>Logo asset: {logoAsset ?? "not uploaded"}</p>
          <p>Sample assets: {sampleAssets.length}</p>
          {isUploading ? <p>Upload progress: {progress}%</p> : null}
          {importingArchive ? <p>Importing archive...</p> : null}
          {importStagedCount !== null ? <p>Archive staged_count: {importStagedCount}</p> : null}
          {importSkippedCount !== null ? <p>Archive skipped_count: {importSkippedCount}</p> : null}
          {Object.keys(progressByFile).length > 0 ? (
            <div className="md:col-span-2">
              <p className="mb-1 text-xs font-medium text-slate-600">Per-file progress</p>
              <ul className="space-y-1 text-xs text-slate-600">
                {Object.entries(progressByFile).map(([name, pct]) => (
                  <li key={name}>
                    {name}: {pct}%
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {error ? <p className="text-red-600">{error.message}</p> : null}
        </div>

        <button
          type="button"
          onClick={() => navigateTo("/onboarding/vocabulary")}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white"
        >
          Continue to vocabulary
        </button>
      </section>
    </main>
  );
}

~~~

## aria-frontend/app/onboarding/company-profile/page.tsx
~~~
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

export default function CompanyProfilePage() {
  const setCompanyId = useCompanyStore((s) => s.setCompanyId);
  const setProfile = useCompanyStore((s) => s.setProfile);

  const form = useForm<CompanyProfileForm>({
    resolver: zodResolver(CompanyProfileSchema),
    defaultValues: {
      company_name: "",
      industry_vertical: "",
      target_market: {
        regions: ["US"],
        segments: ["B2B"],
        persona_summary: ""
      },
      brand_positioning_statement: "",
      tone_of_voice_descriptors: ["confident", "clear", "modern"],
      competitor_list: [],
      platform_presence: {
        instagram: false,
        linkedin: true,
        facebook: false,
        x: true,
        tiktok: false,
        pinterest: false
      },
      posting_frequency_goal: {
        instagram: 3,
        linkedin: 2,
        facebook: 2,
        x: 5,
        tiktok: 2,
        pinterest: 2
      },
      primary_cta_types: ["learn_more"],
      brand_color_hex_codes: ["#0F766E"],
      approved_vocabulary_list: [],
      banned_vocabulary_list: [],
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

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <aside className="space-y-4">
        <OnboardingProgressStepper currentStep={2} score={null} />
        <div className="rounded-xl border bg-white p-4 text-sm text-slate-600">
          Quality threshold: <span className="font-semibold text-slate-900">{ONBOARDING_PASS_THRESHOLD}</span>
        </div>
      </aside>

      <form onSubmit={form.handleSubmit((payload) => mutation.mutate(payload))} className="space-y-6 rounded-2xl border bg-white p-6">
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

~~~

## aria-frontend/app/onboarding/platforms/page.tsx
~~~
// filename: app/onboarding/platforms/page.tsx
// purpose: OAuth platform connection step.

"use client";

import { useEffect, useMemo } from "react";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { getOAuthConnectUrl } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { navigateTo } from "@/lib/navigate";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { Platform } from "@/types";

const platforms: Platform[] = ["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"];

export default function PlatformsPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;
  const credentials = useCompanyStore((s) => s.platformCredentials);
  const updateCredential = useCompanyStore((s) => s.updatePlatformCredential);

  const callback = useMemo(() => {
    if (typeof window === "undefined") {
      return { platform: null, status: null, error: null, account_ref: null, token_expires_at: null };
    }
    const params = new URLSearchParams(window.location.search);
    return {
      platform: params.get("platform"),
      status: params.get("status"),
      error: params.get("error"),
      account_ref: params.get("account_ref"),
      token_expires_at: params.get("token_expires_at")
    };
  }, []);

  useEffect(() => {
    if (!callback.platform) return;
    const platform = callback.platform as Platform;
    if (!platforms.includes(platform)) return;

    if (callback.error === "state_mismatch") {
      updateCredential(platform, { status: "disconnected" });
      return;
    }

    if (callback.status === "connected") {
      updateCredential(platform, {
        status: "connected",
        account_ref: callback.account_ref ?? undefined,
        token_expires_at: callback.token_expires_at ?? undefined,
        updated_at: new Date().toISOString()
      });
    } else if (callback.status === "expired") {
      updateCredential(platform, {
        status: "expired",
        account_ref: callback.account_ref ?? undefined,
        token_expires_at: callback.token_expires_at ?? undefined,
        updated_at: new Date().toISOString()
      });
    }
  }, [callback, updateCredential]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 lg:grid-cols-[300px_1fr]">
      <OnboardingProgressStepper currentStep={9} score={null} />

      <section className="space-y-6 rounded-2xl border bg-white p-6">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Connect platforms</h1>
          <p className="text-sm text-slate-600">Authorize publishing destinations. You can reconnect expired tokens here.</p>
        </header>

        {callback.error === "state_mismatch" ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            OAuth state mismatch detected. Please reconnect from this page.
          </div>
        ) : null}

        <div className="grid gap-3 md:grid-cols-2">
          {platforms.map((platform) => {
            const status = credentials[platform]?.status ?? "disconnected";
            const accountRef = credentials[platform]?.account_ref;
            const tokenExpiresAt = credentials[platform]?.token_expires_at;
            const expiresSoon =
              Boolean(tokenExpiresAt) &&
              new Date(tokenExpiresAt as string).getTime() - Date.now() <= 7 * 24 * 60 * 60 * 1000 &&
              new Date(tokenExpiresAt as string).getTime() > Date.now();
            const color = status === "connected" ? "bg-emerald-100 text-emerald-700" : status === "expired" ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700";

            return (
              <article key={platform} className="rounded-xl border p-4">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-semibold capitalize text-slate-900">{platform}</h2>
                  <span className={`rounded-full px-2 py-1 text-xs ${color}`}>{status}</span>
                </div>
                <a
                  href={getOAuthConnectUrl(platform, companyId)}
                  className="inline-flex rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white"
                >
                  {status === "connected" ? "Reconnect" : "Connect"}
                </a>
                {accountRef ? <p className="mt-2 text-xs text-slate-600">Account: {accountRef}</p> : null}
                {tokenExpiresAt ? <p className="mt-1 text-xs text-slate-500">Token expires: {new Date(tokenExpiresAt).toLocaleString()}</p> : null}
                {expiresSoon ? <p className="mt-1 text-xs text-amber-700">Token expires within 7 days</p> : null}
              </article>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => navigateTo("/onboarding/quality-check")}
          className="rounded-lg bg-teal-700 px-4 py-2 text-sm font-medium text-white"
        >
          Continue to quality check
        </button>
      </section>
    </main>
  );
}

~~~

## aria-frontend/app/onboarding/vocabulary/page.tsx
~~~
// filename: app/onboarding/vocabulary/page.tsx
// purpose: Onboarding vocabulary curation step.

"use client";

import { useState } from "react";
import { toast } from "sonner";

import { OnboardingProgressStepper } from "@/components/onboarding/OnboardingProgressStepper";
import { TagInput } from "@/components/ui/TagInput";
import { updateVocabulary } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { navigateTo } from "@/lib/navigate";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function VocabularyPage() {
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
              navigateTo("/onboarding/platforms");
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

~~~

## aria-frontend/app/page.tsx
~~~
"use client";

import { useEffect } from "react";

import { navigateTo } from "@/lib/navigate";

export default function HomePage() {
  useEffect(() => {
    const redirect = sessionStorage.getItem("redirect");
    if (redirect) {
      sessionStorage.removeItem("redirect");
      window.location.replace(redirect);
      return;
    }

    navigateTo("/login");
  }, []);

  return <main className="mx-auto max-w-4xl px-4 py-10 text-sm text-slate-600">Redirecting...</main>;
}

~~~

## aria-frontend/app/register/page.tsx
~~~
"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { IS_STATIC } from "@/lib/isStatic";
import { AUTH_PREVIEW_MESSAGE } from "@/lib/mockData";
import { getBasePath } from "@/lib/navigate";
import type { UserRole } from "@/types";

const roleOptions: UserRole[] = ["agency_admin", "brand_manager", "content_creator", "analyst"];

export default function RegisterPage() {
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<UserRole | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    role?: string;
    general?: string;
  }>({});

  const emailValid = useMemo(() => /\S+@\S+\.\S+/.test(email), [email]);
  const passwordValid = password.length >= 8;
  const passwordsMatch = password === confirmPassword;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const nextErrors: {
      name?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
      role?: string;
      general?: string;
    } = {};

    if (!name.trim()) {
      nextErrors.name = "Full name is required.";
    }

    if (!emailValid) {
      nextErrors.email = "Please enter a valid email address.";
    }
    if (!passwordValid) {
      nextErrors.password = "Password must be at least 8 characters.";
    }
    if (!passwordsMatch) {
      nextErrors.confirmPassword = "Confirm password must match password.";
    }
    if (!role) {
      nextErrors.role = "Please select a role.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register({ name: name.trim(), email: email.trim(), password, role: role as UserRole });
      window.location.href = `${getBasePath()}/login?registered=1`;
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : "Failed to create account.";
      setErrors((prev) => ({
        ...prev,
        general: IS_STATIC ? AUTH_PREVIEW_MESSAGE : message.includes("exists") ? "Email already exists." : message
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center px-4 py-8">
      <section className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl md:grid-cols-2">
        <div className="bg-gradient-to-br from-teal-700 via-sky-700 to-cyan-700 p-8 text-white">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">ARIA Console</p>
          <h1 className="mt-3 text-3xl font-semibold">Scale your social pipeline</h1>
          <p className="mt-4 text-sm text-cyan-100">Generate platform-native content, review quality signals, and schedule with confidence.</p>
        </div>

        <form onSubmit={submit} className="space-y-4 p-8">
          <h2 className="text-xl font-semibold text-slate-900">Create account</h2>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Full Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Jane Doe"
            />
            {errors.name ? <p className="text-xs text-red-600">{errors.name}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="you@company.com"
            />
            {errors.email ? <p className="text-xs text-red-600">{errors.email}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
            {errors.password ? <p className="text-xs text-red-600">{errors.password}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Confirm Password</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
            {errors.confirmPassword ? <p className="text-xs text-red-600">{errors.confirmPassword}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole | "")}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">Select role</option>
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.role ? <p className="text-xs text-red-600">{errors.role}</p> : null}
          </label>

          {errors.general ? <p className="text-xs text-red-600">{errors.general}</p> : null}

          {IS_STATIC ? (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">{AUTH_PREVIEW_MESSAGE}</p>
          ) : null}

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>

          <p className="text-sm text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-slate-900 underline">
              Sign in
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}

~~~

## aria-frontend/context/AuthContext.tsx
~~~
"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { mockUser } from "@/lib/mockData";
import { getBasePath } from "@/lib/navigate";
import type { UserRole } from "@/types";

interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
}

interface LoginInput {
  email: string;
  password: string;
}

interface RegisterInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (input: LoginInput) => Promise<AuthUser>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  continueAsPreviewUser: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as { error?: string };
    return payload.error ?? "Request failed";
  } catch {
    return "Request failed";
  }
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const readUserFromStorage = useCallback((): AuthUser | null => {
    if (typeof window === "undefined") {
      return null;
    }

    const stored = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (!stored || !token) {
      return null;
    }

    try {
      return JSON.parse(stored) as AuthUser;
    } catch {
      localStorage.clear();
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(readUserFromStorage());
    setIsLoading(false);
  }, [readUserFromStorage]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const stored = localStorage.getItem("user");
      const token = localStorage.getItem("token");
      if (stored && token) {
        setUser(JSON.parse(stored) as AuthUser);
      }
    } catch {
      localStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify(input)
    });

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
    }

    const payload = (await response.json()) as { user: AuthUser; token: string };
    if (typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(payload.user));
      localStorage.setItem("token", payload.token);
    }
    setUser(payload.user);
    return payload.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(input)
    });

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
    }
  }, []);

  const logout = useCallback(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      localStorage.removeItem("isPreview");
      window.location.href = `${getBasePath()}/login`;
    }
    setUser(null);
  }, []);

  const continueAsPreviewUser = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    localStorage.setItem("user", JSON.stringify(mockUser));
    localStorage.setItem("token", "preview-token-static-mode");
    localStorage.setItem("isPreview", "true");
    localStorage.setItem("aria_company_id", "preview-company");
    localStorage.setItem("aria_role", mockUser.role);
    setUser(mockUser);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser,
      continueAsPreviewUser
    }),
    [continueAsPreviewUser, isLoading, login, logout, refreshUser, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

~~~

## aria-frontend/hooks/useRequireAuth.ts
~~~
"use client";

import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { getBasePath } from "@/lib/navigate";

export const useRequireAuth = () => {
  const auth = useAuth();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const user = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (!user || !token) {
      window.location.href = `${getBasePath()}/login`;
      return;
    }

    try {
      JSON.parse(user);
    } catch {
      window.location.href = `${getBasePath()}/login`;
      return;
    }

    if (!auth.user) {
      void auth.refreshUser();
    }
  }, [auth.refreshUser, auth.user]);

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated && typeof window !== "undefined") {
      window.location.href = `${getBasePath()}/login`;
    }
  }, [auth.isAuthenticated, auth.isLoading]);

  return auth;
};

~~~

## aria-frontend/lib/navigate.ts
~~~
const BASE_PATH = '/AI-Social-Media-Manager';

export const navigateTo = (path: string) => {
  if (typeof window !== 'undefined') {
    window.location.href = BASE_PATH + path;
  }
};

export const getBasePath = () => BASE_PATH;
~~~

## aria-frontend/middleware.ts
~~~
export function middleware() {}
export const config = { matcher: [] };

~~~

## aria-frontend/public/404.html
~~~
<!DOCTYPE html>
<html>
<head>
  <script>
    const path = window.location.pathname;
    const base = '/AI-Social-Media-Manager';
    if (path.startsWith(base)) {
      sessionStorage.setItem('redirect', path);
      window.location.replace(base + '/');
    }
  </script>
</head>
<body></body>
</html>

~~~

