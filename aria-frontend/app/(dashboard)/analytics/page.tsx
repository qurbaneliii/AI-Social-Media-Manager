// filename: app/(dashboard)/analytics/page.tsx
// purpose: Audit and quality analytics view.

"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AudienceConfidenceBadge } from "@/components/audience/AudienceConfidenceBadge";
import { QUALITY_SCORE_THRESHOLDS } from "@/config/constants";
import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getAuditLog } from "@/lib/api";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function AnalyticsPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;

  const auditQuery = useQuery({
    queryKey: ["audit-log", companyId],
    queryFn: () => getAuditLog(companyId as string, 50, 0),
    enabled: Boolean(companyId)
  });

  const postsQuery = useCompanyPosts(companyId, 0);

  const qualityData = useMemo(() => {
    return (postsQuery.data ?? []).map((post) => ({
      id: post.post_id.slice(0, 8),
      quality: post.generated_package_json?.content_quality_score?.overall ?? 0
    }));
  }, [postsQuery.data]);

  const avgConfidence = useMemo(() => {
    const rows = postsQuery.data ?? [];
    if (rows.length === 0) return 0;
    const total = rows.reduce((acc, post) => acc + (post.generated_package_json?.audience_definition?.confidence ?? 0), 0);
    return total / rows.length;
  }, [postsQuery.data]);

  if (!companyId) {
    return <div className="rounded-xl border bg-white p-6 text-sm text-red-700">Company ID is required. Return to sign in.</div>;
  }

  return (
    <main className="space-y-6 rounded-2xl border bg-white p-6">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900">Analytics</h1>
        <p className="text-sm text-slate-600">Review quality trends, audience confidence, and audit activity.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Posts analyzed</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{postsQuery.data?.length ?? 0}</p>
        </article>
        <article className="rounded-xl border p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Audit events</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{auditQuery.data?.length ?? 0}</p>
        </article>
        <article className="rounded-xl border p-4">
          <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Audience confidence</p>
          <AudienceConfidenceBadge confidence={avgConfidence} />
        </article>
      </section>

      {avgConfidence < 0.55 ? (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          Audience confidence is low. Consider refreshing audience inputs before auto-publishing.
        </div>
      ) : null}

      <section className="rounded-xl border p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Quality score by post</h2>
        {qualityData.length === 0 ? (
          <p className="text-sm text-slate-600">No generated posts yet.</p>
        ) : (
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={qualityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="id" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="quality" fill="#0d9488" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Quality guidance</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
          <li>Good threshold: {QUALITY_SCORE_THRESHOLDS.good}+</li>
          <li>Warning threshold: {QUALITY_SCORE_THRESHOLDS.warning}+</li>
        </ul>
      </section>
    </main>
  );
}
