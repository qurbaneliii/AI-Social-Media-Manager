"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AlertTriangle, ArrowRight, Brain, CalendarClock, FileText, Plus, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardFeed } from "@/hooks/useDashboardFeed";
import { getOverview } from "@/lib/api";
import { getBrandProfile } from "@/lib/api/ai-workspace";
import { getClientSession } from "@/lib/client-session";
import { useDashboardStore } from "@/lib/store";

const previewModeEnabled = process.env.NEXT_PUBLIC_PREVIEW_MODE === "true";

const statusLabel = (status: string): string => {
  if (status === "scheduled") {
    return "Internal plan";
  }
  if (status === "published") {
    return "Imported published state";
  }
  return status.charAt(0).toUpperCase() + status.slice(1);
};

export default function BrandDashboardPage() {
  const feed = useDashboardFeed();
  const brandProfile = useDashboardStore((state) => state.brandProfile);
  const companyId = feed.companyId ?? getClientSession().companyId;
  const overview = useQuery({ queryKey: ["overview"], queryFn: getOverview, enabled: Boolean(companyId) });
  const brand = useQuery({ queryKey: ["brand-profile", companyId], queryFn: () => getBrandProfile(companyId!), enabled: Boolean(companyId), retry: false });

  const summary = overview.data?.summary;
  const drafts = summary?.drafts ?? 0;
  const failed = summary?.failed_generations ?? 0;
  const planned = overview.data?.upcoming_plans ?? [];
  const completeness = brand.data?.validation.completeness_score ?? 0;
  const recent = feed.posts.slice(0, 4);

  if (feed.isLoading || overview.isLoading) {
    return (
      <div className="space-y-6" aria-busy="true" aria-label="Loading Overview">
        <Skeleton className="h-24" />
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-4 border-b border-[var(--border)] pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="default">{brandProfile.companyName}</Badge>
            {previewModeEnabled ? <Badge variant="warning">Demo data</Badge> : <Badge variant="info">Workspace data</Badge>}
          </div>
          <div>
            <h1>Overview</h1>
            <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">
              Prioritize brand readiness, content review, and internal planning from one workspace.
            </p>
          </div>
        </div>
        <Button asChild>
          <Link href="/posts/new">
            <Plus className="h-4 w-4" />
            Create content
          </Link>
        </Button>
      </header>

      <section aria-labelledby="operational-summary-title" className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <h2 id="operational-summary-title">Operational summary</h2>
          <p className="text-xs text-[var(--text-muted)]">Current workspace state</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: "Draft content", value: drafts, icon: FileText, note: "Awaiting refinement or review" },
            { label: "Failed workflows", value: failed, icon: AlertTriangle, note: "Needs investigation" },
            { label: "Approved plans", value: summary?.approved_internal_plans ?? 0, icon: CalendarClock, note: "Internal planning only" },
            { label: "Brand Brain", value: `${completeness}%`, icon: Brain, note: "Persisted profile completeness" }
          ].map((metric) => {
            const Icon = metric.icon;
            return (
              <Card key={metric.label} className="rounded-lg shadow-none">
                <CardContent className="flex items-start justify-between gap-4 p-4">
                  <div>
                    <p className="text-xs font-medium text-[var(--text-muted)]">{metric.label}</p>
                    <p className="mt-2 text-2xl font-semibold tabular-nums">{metric.value}</p>
                    <p className="mt-1 text-xs text-[var(--text-secondary)]">{metric.note}</p>
                  </div>
                  <span className="grid h-9 w-9 place-items-center rounded-md bg-[var(--bg-elevated)] text-[var(--brand-primary)]">
                    <Icon className="h-4 w-4" />
                  </span>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <div className="grid gap-8 xl:grid-cols-[minmax(0,1.5fr)_minmax(300px,0.75fr)]">
        <section aria-labelledby="recent-content-title" className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 id="recent-content-title">Recent content</h2>
            <Button asChild variant="ghost" size="sm">
              <Link href="/posts">
                View library
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>

          {recent.length ? (
            <div className="divide-y divide-[var(--border)] border-y border-[var(--border)]">
              {recent.map((post) => (
                <article key={post.id} className="grid gap-3 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                  <div className="min-w-0">
                    <div className="mb-2 flex flex-wrap items-center gap-2">
                      <Badge variant="info">{post.platform === "twitter" ? "X" : post.platform}</Badge>
                      <Badge variant={post.status === "failed" ? "danger" : post.status === "draft" ? "default" : "warning"}>
                        {statusLabel(post.status)}
                      </Badge>
                      {previewModeEnabled ? <Badge variant="warning">Demo</Badge> : null}
                    </div>
                    <p className="line-clamp-2 text-sm leading-6 text-[var(--text-secondary)]">{post.content}</p>
                  </div>
                  <Button asChild variant="outline" size="sm">
                    <Link href="/posts">Open</Link>
                  </Button>
                </article>
              ))}
            </div>
          ) : (
            <div className="border-y border-[var(--border)] py-12 text-center">
              <FileText className="mx-auto h-6 w-6 text-[var(--text-muted)]" />
              <p className="mt-3 text-sm font-medium">No content yet</p>
              <p className="mt-1 text-sm text-[var(--text-secondary)]">Create a draft to begin the review workflow.</p>
              <Button asChild size="sm" className="mt-4">
                <Link href="/posts/new">Create draft</Link>
              </Button>
            </div>
          )}
        </section>

        <section aria-labelledby="needs-attention-title" className="space-y-3">
          <h2 id="needs-attention-title">Needs attention</h2>
          <div className="space-y-2">
            {completeness < 100 ? (
              <Link href="/dashboard/brand-brain" className="flex min-h-11 items-center gap-3 rounded-lg border border-[var(--border)] p-3 hover:bg-[var(--bg-hover)]">
                <Brain className="h-4 w-4 text-[var(--warning)]" />
                <span className="min-w-0 flex-1 text-sm">Complete Brand Brain ({completeness}%)</span>
                <ArrowRight className="h-4 w-4 text-[var(--text-muted)]" />
              </Link>
            ) : null}
            {failed > 0 ? (
              <Link href="/posts" className="flex min-h-11 items-center gap-3 rounded-lg border border-[var(--border)] p-3 hover:bg-[var(--bg-hover)]">
                <AlertTriangle className="h-4 w-4 text-[var(--danger)]" />
                <span className="min-w-0 flex-1 truncate text-sm">{failed} failed content workflow{failed === 1 ? "" : "s"}</span>
                <ArrowRight className="h-4 w-4 text-[var(--text-muted)]" />
              </Link>
            ) : null}
            {failed === 0 && completeness >= 100 ? (
              <div className="flex items-center gap-3 rounded-lg border border-[var(--border)] p-3 text-sm text-[var(--text-secondary)]">
                <ShieldCheck className="h-4 w-4 text-[var(--success)]" />
                No urgent workspace issues.
              </div>
            ) : null}
          </div>

          <div className="pt-4">
            <div className="flex items-center justify-between gap-3">
              <h2>Upcoming content</h2>
              <Badge variant="default">Internal plans</Badge>
            </div>
            {planned.length ? (
              <div className="mt-3 space-y-2">
                {planned.slice(0, 3).map((post) => (
                  <div key={String(post.calendar_item_id)} className="rounded-lg border border-[var(--border)] p-3">
                    <p className="line-clamp-2 text-sm text-[var(--text-secondary)]">{String(post.platform ?? "Content plan")}</p>
                    <p className="mt-2 text-xs text-[var(--text-muted)]">
                      {post.planned_at ? new Date(String(post.planned_at)).toLocaleString() : "Planning date not set"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-[var(--text-secondary)]">No approved internal plans are ready for the calendar.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
