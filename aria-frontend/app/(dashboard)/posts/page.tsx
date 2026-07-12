"use client";

import { AlertCircle, ArrowRight, CalendarClock, ChevronLeft, ChevronRight, FileText, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";
import type { Platform, PostResult } from "@/types";

type StatusFilter = "all" | PostResult["status"];
type PlatformFilter = "all" | Platform;

const statusStyles: Record<PostResult["status"], string> = {
  generated: "border-emerald-200 bg-emerald-50 text-emerald-800",
  generating: "border-sky-200 bg-sky-50 text-sky-800",
  failed: "border-red-200 bg-red-50 text-red-800"
};

function getPrimaryVariant(post: PostResult) {
  const variants = post.generated_package_json?.variants ?? [];
  return variants.find((variant) => variant.variant_id === post.generated_package_json?.selected_variant_id) ?? variants[0];
}

function ContentItem({ post }: { post: PostResult }) {
  const variant = getPrimaryVariant(post);
  const quality = post.generated_package_json?.content_quality_score?.overall;

  return (
    <article className="grid gap-4 border-b border-[var(--border)] py-5 last:border-b-0 md:grid-cols-[minmax(0,1fr)_auto] md:items-start">
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className={`rounded border px-2 py-1 text-xs font-semibold capitalize ${statusStyles[post.status]}`}>
            {post.status}
          </span>
          {variant?.platform ? (
            <span className="rounded border border-[var(--border)] bg-[var(--bg-secondary)] px-2 py-1 text-xs font-medium capitalize text-[var(--text-secondary)]">
              {variant.platform}
            </span>
          ) : null}
          <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800">Demo data</span>
        </div>

        <p className="max-w-3xl whitespace-pre-wrap text-sm leading-6 text-[var(--text-primary)]">
          {variant?.text || (post.status === "failed" ? "This generation did not produce content." : "Content is still being prepared.")}
        </p>

        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-muted)]">
          {typeof quality === "number" ? <span>Quality score {Math.round(quality)}</span> : null}
          <span title={post.post_id}>ID {post.post_id.slice(0, 8)}</span>
        </div>
      </div>

      <div className="flex items-center gap-2 md:justify-end">
        <Link
          href={`/posts/${post.post_id}/result`}
          className="inline-flex min-h-11 items-center gap-2 rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm font-semibold text-[var(--text-primary)] hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
        >
          Review <ArrowRight aria-hidden="true" className="size-4" />
        </Link>
        {post.status === "generated" ? (
          <Link
            href={`/posts/${post.post_id}/schedule`}
            aria-label="Plan this content on the calendar"
            title="Plan on calendar"
            className="inline-flex size-11 items-center justify-center rounded border border-[var(--border-strong)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]"
          >
            <CalendarClock aria-hidden="true" className="size-4" />
          </Link>
        ) : null}
      </div>
    </article>
  );
}

export default function PostsPage() {
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [platform, setPlatform] = useState<PlatformFilter>("all");
  const companyId = useCompanyStore((state) => state.companyId) ?? getClientSession().companyId;
  const query = useCompanyPosts(companyId, page);

  const posts = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    return (query.data ?? []).filter((post) => {
      const variants = post.generated_package_json?.variants ?? [];
      const matchesSearch = !normalizedSearch || post.post_id.toLowerCase().includes(normalizedSearch) || variants.some((item) => item.text.toLowerCase().includes(normalizedSearch));
      const matchesStatus = status === "all" || post.status === status;
      const matchesPlatform = platform === "all" || variants.some((item) => item.platform === platform);
      return matchesSearch && matchesStatus && matchesPlatform;
    });
  }, [platform, query.data, search, status]);

  if (!companyId) {
    return (
      <div className="surface-card flex items-start gap-3 rounded p-5 text-sm text-red-700" role="alert">
        <AlertCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
        <span>Company context is missing. Sign in again to restore your workspace.</span>
      </div>
    );
  }

  return (
    <section className="mx-auto w-full max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="label-xs mb-2">Content workspace</p>
          <h1>Content</h1>
          <p className="mt-1 max-w-2xl text-sm text-[var(--text-secondary)]">Review drafts, compare generated content, and move approved work into planning.</p>
        </div>
        <Link href="/posts/new" className="inline-flex min-h-11 items-center justify-center gap-2 rounded bg-teal-700 px-4 text-sm font-semibold text-white hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring)]">
          <Plus aria-hidden="true" className="size-4" /> New content
        </Link>
      </header>

      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto_auto]">
        <label className="relative block">
          <span className="sr-only">Search content</span>
          <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--text-muted)]" />
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search drafts" className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] pl-10 pr-3 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--focus-ring)] focus:ring-2 focus:ring-[var(--focus-ring)]/20" />
        </label>
        <label>
          <span className="sr-only">Filter by status</span>
          <select value={status} onChange={(event) => setStatus(event.target.value as StatusFilter)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--focus-ring)] sm:w-40">
            <option value="all">All statuses</option><option value="generated">Generated</option><option value="generating">Generating</option><option value="failed">Failed</option>
          </select>
        </label>
        <label>
          <span className="sr-only">Filter by platform</span>
          <select value={platform} onChange={(event) => setPlatform(event.target.value as PlatformFilter)} className="min-h-11 w-full rounded border border-[var(--border-strong)] bg-[var(--bg-surface)] px-3 text-sm text-[var(--text-primary)] outline-none focus:border-[var(--focus-ring)] sm:w-40">
            <option value="all">All platforms</option><option value="instagram">Instagram</option><option value="linkedin">LinkedIn</option><option value="facebook">Facebook</option><option value="x">X</option><option value="tiktok">TikTok</option>
          </select>
        </label>
      </div>

      <div className="surface-card rounded px-4 sm:px-6" aria-live="polite" aria-busy={query.isLoading}>
        {query.isLoading ? <p className="py-10 text-center text-sm text-[var(--text-secondary)]">Loading content...</p> : null}
        {query.isError ? <p className="py-10 text-center text-sm text-red-700">Content could not be loaded. Try again shortly.</p> : null}
        {!query.isLoading && !query.isError && posts.length === 0 ? (
          <div className="flex flex-col items-center px-4 py-12 text-center">
            <FileText aria-hidden="true" className="mb-3 size-8 text-[var(--text-muted)]" />
            <h2 className="text-base">No content found</h2>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">Adjust your filters or create a new draft.</p>
          </div>
        ) : null}
        {posts.map((post) => <ContentItem key={post.post_id} post={post} />)}
      </div>

      <nav className="flex items-center justify-between" aria-label="Content pages">
        <button type="button" disabled={page === 0} className="inline-flex min-h-11 items-center gap-2 rounded border border-[var(--border-strong)] px-3 text-sm font-medium disabled:opacity-40" onClick={() => setPage((current) => Math.max(0, current - 1))}><ChevronLeft aria-hidden="true" className="size-4" /> Previous</button>
        <span className="text-sm text-[var(--text-secondary)]">Page {page + 1}</span>
        <button type="button" disabled={!query.data || query.data.length < 20} className="inline-flex min-h-11 items-center gap-2 rounded border border-[var(--border-strong)] px-3 text-sm font-medium disabled:opacity-40" onClick={() => setPage((current) => current + 1)}>Next <ChevronRight aria-hidden="true" className="size-4" /></button>
      </nav>
    </section>
  );
}
