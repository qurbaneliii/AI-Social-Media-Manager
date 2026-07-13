"use client";

import { Activity, AlertCircle, ArrowRight, BarChart3, Brain, FileText, History } from "lucide-react";
import Link from "next/link";
import { useMemo } from "react";

import { SkeletonBlock } from "@/components/ui/SkeletonBlock";
import { QUALITY_SCORE_THRESHOLDS } from "@/config/constants";
import { useAuditLog } from "@/hooks/useAuditLog";
import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";

function DataSourceBadge({ children }: { children: React.ReactNode }) {
  return <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-800">{children}</span>;
}

export default function AnalyticsPage() {
  const previewMode = process.env.NEXT_PUBLIC_PREVIEW_MODE === "true" || process.env.PREVIEW_MODE === "true";
  const companyId = useCompanyStore((state) => state.companyId) ?? getClientSession().companyId;
  const auditQuery = useAuditLog(companyId, 0, 50);
  const postsQuery = useCompanyPosts(companyId, 0);
  const isLoading = auditQuery.isLoading || postsQuery.isLoading;

  const qualityData = useMemo(() => (postsQuery.data ?? []).map((post) => ({
    id: post.post_id,
    label: post.generated_package_json?.variants?.[0]?.platform ?? "content",
    score: Math.round(post.generated_package_json?.content_quality_score?.overall ?? 0)
  })), [postsQuery.data]);

  const averageQuality = qualityData.length ? Math.round(qualityData.reduce((sum, item) => sum + item.score, 0) / qualityData.length) : 0;
  const averageConfidence = useMemo(() => {
    const posts = postsQuery.data ?? [];
    if (!posts.length) return 0;
    return Math.round((posts.reduce((sum, post) => sum + (post.generated_package_json?.audience_definition?.confidence ?? 0), 0) / posts.length) * 100);
  }, [postsQuery.data]);

  if (!companyId) {
    return <div className="surface-card flex items-start gap-3 rounded p-5 text-sm text-red-700" role="alert"><AlertCircle aria-hidden="true" className="mt-0.5 size-5" /> Company context is missing. Sign in again to restore your workspace.</div>;
  }

  return (
    <section className="mx-auto w-full max-w-6xl space-y-7">
      <header>
        <p className="label-xs mb-2">Decision support</p>
        <h1>Insights</h1>
        <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">Understand generated content quality and workflow activity without confusing internal estimates with live platform analytics.</p>
        {previewMode ? <div className="mt-3"><DataSourceBadge>Demo data</DataSourceBadge></div> : null}
      </header>

      <div className="rounded border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
        <div className="flex items-start gap-3"><Activity aria-hidden="true" className="mt-0.5 size-5 shrink-0" /><p><strong>Internal data only.</strong> Live engagement, reach, and follower metrics will appear only after a verified platform integration supplies them.</p></div>
      </div>

      <dl className="grid border-y border-[var(--border)] sm:grid-cols-3">
        <div className="py-5 sm:pr-6"><dt className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><FileText aria-hidden="true" className="size-4" /> Generated packages</dt><dd className="mt-2 text-3xl font-bold">{isLoading ? <SkeletonBlock className="h-9 w-14 rounded" /> : qualityData.length}</dd><p className="mt-1 text-xs text-[var(--text-muted)]">Source: internal generation records</p></div>
        <div className="border-t border-[var(--border)] py-5 sm:border-l sm:border-t-0 sm:px-6"><dt className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><BarChart3 aria-hidden="true" className="size-4" /> Average quality</dt><dd className="mt-2 text-3xl font-bold">{isLoading ? <SkeletonBlock className="h-9 w-14 rounded" /> : `${averageQuality}/100`}</dd><p className="mt-1 text-xs text-[var(--text-muted)]">Source: AI quality estimate</p></div>
        <div className="border-t border-[var(--border)] py-5 sm:border-l sm:border-t-0 sm:pl-6"><dt className="flex items-center gap-2 text-sm text-[var(--text-secondary)]"><Brain aria-hidden="true" className="size-4" /> Audience confidence</dt><dd className="mt-2 text-3xl font-bold">{isLoading ? <SkeletonBlock className="h-9 w-14 rounded" /> : `${averageConfidence}%`}</dd><p className="mt-1 text-xs text-[var(--text-muted)]">Source: generated audience model</p></div>
      </dl>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="external-performance-heading">
        <div className="flex flex-wrap items-start justify-between gap-3"><div><h2 id="external-performance-heading">External performance</h2><p className="mt-1 text-sm text-[var(--text-secondary)]">Engagement, reach, impressions, clicks, and follower growth.</p></div><span className="rounded border border-slate-300 bg-[var(--bg-secondary)] px-2 py-1 text-xs font-semibold text-[var(--text-secondary)]">Unavailable</span></div>
        <p className="mt-4 text-sm text-[var(--text-secondary)]">Source: no verified social-platform analytics integration is configured. ARIA does not render zero-filled charts as performance data.</p>
      </section>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="quality-heading">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div><h2 id="quality-heading">Content quality</h2><p className="mt-1 text-sm text-[var(--text-secondary)]">Model-generated review scores, not external performance.</p></div>
          <DataSourceBadge>AI estimate</DataSourceBadge>
        </div>

        {isLoading ? <div className="space-y-4"><SkeletonBlock className="h-10 w-full rounded" /><SkeletonBlock className="h-10 w-full rounded" /></div> : null}
        {!isLoading && qualityData.length === 0 ? (
          <div className="py-8 text-center"><BarChart3 aria-hidden="true" className="mx-auto mb-3 size-8 text-[var(--text-muted)]" /><h3>No quality data yet</h3><p className="mt-1 text-sm text-[var(--text-secondary)]">Generate content to see internal quality checks.</p><Link href="/posts/new" className="mt-4 inline-flex min-h-11 items-center gap-2 rounded border border-[var(--border-strong)] px-4 text-sm font-semibold">Create content <ArrowRight aria-hidden="true" className="size-4" /></Link></div>
        ) : null}
        <ul className="space-y-5">
          {qualityData.slice(0, 8).map((item) => (
            <li key={item.id}>
              <div className="mb-2 flex items-center justify-between gap-4 text-sm"><span className="min-w-0 truncate capitalize text-[var(--text-secondary)]">{item.label} draft <span className="text-[var(--text-muted)]">#{item.id.slice(0, 8)}</span></span><strong>{item.score}/100</strong></div>
              <div className="h-2 overflow-hidden rounded bg-[var(--bg-muted)]" role="img" aria-label={`Quality score ${item.score} out of 100`}><div className={`h-full rounded ${item.score >= QUALITY_SCORE_THRESHOLDS.good ? "bg-emerald-600" : item.score >= QUALITY_SCORE_THRESHOLDS.warning ? "bg-amber-500" : "bg-red-600"}`} style={{ width: `${Math.min(100, Math.max(0, item.score))}%` }} /></div>
            </li>
          ))}
        </ul>
      </section>

      <section className="surface-card rounded p-5 sm:p-6" aria-labelledby="activity-heading">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><h2 id="activity-heading">Recent workflow activity</h2><p className="mt-1 text-sm text-[var(--text-secondary)]">Trusted audit events from this workspace.</p></div><span className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-2 py-1 text-xs font-semibold text-[var(--text-secondary)]">Audit log</span></div>
        {isLoading ? <div className="space-y-3"><SkeletonBlock className="h-14 w-full rounded" /><SkeletonBlock className="h-14 w-full rounded" /></div> : null}
        {!isLoading && !auditQuery.data?.length ? <div className="py-8 text-center"><History aria-hidden="true" className="mx-auto mb-3 size-8 text-[var(--text-muted)]" /><h3>No audit events yet</h3><p className="mt-1 text-sm text-[var(--text-secondary)]">Generation, approval, and planning actions will appear here.</p></div> : null}
        <ol className="divide-y divide-[var(--border)]">
          {auditQuery.data?.slice(0, 10).map((item, index) => (
            <li key={`${item.created_at ?? index}-${index}`} className="grid gap-1 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
              <div className="min-w-0"><p className="text-sm font-medium text-[var(--text-primary)]">{item.action ?? "Workflow activity"}</p><p className="truncate text-xs text-[var(--text-secondary)]">{item.resource_type ?? "workspace"} by {item.actor ?? "system"}</p></div>
              <time className="text-xs text-[var(--text-muted)]" dateTime={item.created_at ?? undefined}>{item.created_at ? new Date(item.created_at).toLocaleString() : "Time unavailable"}</time>
            </li>
          ))}
        </ol>
      </section>
    </section>
  );
}
