// filename: app/(dashboard)/analytics/page.tsx
// purpose: Audit and quality analytics view.

"use client";

import { Fragment, useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { AudienceConfidenceBadge } from "@/components/audience/AudienceConfidenceBadge";
import { QUALITY_SCORE_THRESHOLDS } from "@/config/constants";
import { useAuditLog } from "@/hooks/useAuditLog";
import { useCompanyPosts } from "@/hooks/useCompanyPosts";
import { getClientSession } from "@/lib/client-session";
import { useCompanyStore } from "@/stores/useCompanyStore";

export default function AnalyticsPage() {
  const companyId = useCompanyStore((s) => s.companyId) ?? getClientSession().companyId;

  const auditQuery = useAuditLog(companyId, 0, 50);

  const postsQuery = useCompanyPosts(companyId, 0);

  const qualityData = useMemo(() => {
    return (postsQuery.data ?? []).map((post) => ({
      id: post.post_id.slice(0, 8),
      quality: post.generated_package_json?.content_quality_score?.overall ?? 0,
      posting_timestamp: (post as any).posting_timestamp ?? (post as any).created_at ?? post.post_id
    }));
  }, [postsQuery.data]);

  const engagementSeries = useMemo(() => {
    const rows = postsQuery.data ?? [];
    return rows.map((post) => {
      const metrics = ((post as any).performance_metrics ?? {}) as Record<string, number>;
      const perPlatform = ((post as any).platform_metrics ?? {}) as Record<string, { engagement_rate?: number }>;
      return {
        posting_timestamp: (post as any).posting_timestamp ?? (post as any).created_at ?? post.post_id,
        engagement_rate: metrics.engagement_rate ?? 0,
        instagram: perPlatform.instagram?.engagement_rate ?? 0,
        linkedin: perPlatform.linkedin?.engagement_rate ?? 0,
        facebook: perPlatform.facebook?.engagement_rate ?? 0,
        x: perPlatform.x?.engagement_rate ?? 0,
        tiktok: perPlatform.tiktok?.engagement_rate ?? 0,
        pinterest: perPlatform.pinterest?.engagement_rate ?? 0
      };
    });
  }, [postsQuery.data]);

  const frequencySeries = useMemo(() => {
    const rows = postsQuery.data ?? [];
    const bucket = new Map<
      string,
      {
        week: string;
        instagram: number;
        linkedin: number;
        facebook: number;
        x: number;
        tiktok: number;
        pinterest: number;
      }
    >();
    rows.forEach((post) => {
      const timestamp = (post as any).posting_timestamp ?? (post as any).created_at;
      if (!timestamp) return;
      const date = new Date(timestamp);
      const weekKey = `${date.getUTCFullYear()}-W${Math.ceil((date.getUTCDate() + 6 - date.getUTCDay()) / 7)}`;
      if (!bucket.has(weekKey)) {
        bucket.set(weekKey, {
          week: weekKey,
          instagram: 0,
          linkedin: 0,
          facebook: 0,
          x: 0,
          tiktok: 0,
          pinterest: 0
        });
      }
      const entry = bucket.get(weekKey);
      if (!entry) return;
      const targets = ((post as any).platform_targets ?? []) as string[];
      targets.forEach((target) => {
        if (target in entry) {
          (entry[target as keyof typeof entry] as number) += 1;
        }
      });
    });
    return Array.from(bucket.values());
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
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Engagement rate over time per platform</h2>
        {engagementSeries.length === 0 ? (
          <p className="text-sm text-slate-600">No engagement metrics available.</p>
        ) : (
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={engagementSeries}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="posting_timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="instagram" stroke="#ec4899" dot={false} />
                <Line type="monotone" dataKey="linkedin" stroke="#2563eb" dot={false} />
                <Line type="monotone" dataKey="facebook" stroke="#1d4ed8" dot={false} />
                <Line type="monotone" dataKey="x" stroke="#111827" dot={false} />
                <Line type="monotone" dataKey="tiktok" stroke="#14b8a6" dot={false} />
                <Line type="monotone" dataKey="pinterest" stroke="#be123c" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Posting frequency by platform per week</h2>
        {frequencySeries.length === 0 ? (
          <p className="text-sm text-slate-600">No posting frequency data available.</p>
        ) : (
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={frequencySeries}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar stackId="a" dataKey="instagram" fill="#ec4899" />
                <Bar stackId="a" dataKey="linkedin" fill="#2563eb" />
                <Bar stackId="a" dataKey="facebook" fill="#1d4ed8" />
                <Bar stackId="a" dataKey="x" fill="#111827" />
                <Bar stackId="a" dataKey="tiktok" fill="#14b8a6" />
                <Bar stackId="a" dataKey="pinterest" fill="#be123c" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Posts and performance metrics</h2>
        {postsQuery.data?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Post</th>
                  <th className="px-2 py-2">Quality score</th>
                  <th className="px-2 py-2">Platform targets</th>
                  <th className="px-2 py-2">Status</th>
                  <th className="px-2 py-2">Created at</th>
                </tr>
              </thead>
              <tbody>
                {postsQuery.data.map((post) => {
                  const row = post as any;
                  const metrics = (row.performance_metrics ?? {}) as Record<string, number>;
                  return (
                    <Fragment key={post.post_id}>
                      <tr className="border-b">
                        <td className="px-2 py-2 font-mono text-xs">{post.post_id}</td>
                        <td className="px-2 py-2">{post.generated_package_json?.content_quality_score?.overall ?? 0}</td>
                        <td className="px-2 py-2">{(row.platform_targets ?? []).join(", ") || "-"}</td>
                        <td className="px-2 py-2">{post.status}</td>
                        <td className="px-2 py-2">{row.created_at ? new Date(row.created_at).toLocaleString() : "-"}</td>
                      </tr>
                      <tr className="border-b bg-slate-50">
                        <td className="px-2 py-2 text-xs text-slate-700" colSpan={5}>
                          impressions {metrics.impressions ?? 0} | reach {metrics.reach ?? 0} | engagement_rate {metrics.engagement_rate ?? 0} |
                          click_through_rate {metrics.click_through_rate ?? 0} | saves {metrics.saves ?? 0} | shares {metrics.shares ?? 0} |
                          follower_growth_delta {metrics.follower_growth_delta ?? 0}
                        </td>
                      </tr>
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-600">No posts available.</p>
        )}
      </section>

      <section className="rounded-xl border p-4">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Audit log</h2>
        {auditQuery.data?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Actor</th>
                  <th className="px-2 py-2">Action</th>
                  <th className="px-2 py-2">Resource</th>
                  <th className="px-2 py-2">Created at</th>
                </tr>
              </thead>
              <tbody>
                {auditQuery.data.map((item: any, idx: number) => (
                  <tr key={`${item.created_at ?? idx}-${idx}`} className="border-b">
                    <td className="px-2 py-2">{item.actor ?? "system"}</td>
                    <td className="px-2 py-2">{item.action ?? "-"}</td>
                    <td className="px-2 py-2">{item.resource_type ?? "-"}</td>
                    <td className="px-2 py-2">{item.created_at ? new Date(item.created_at).toLocaleString() : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-600">No audit events found.</p>
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
