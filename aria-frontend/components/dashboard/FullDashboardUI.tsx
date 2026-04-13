"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";

import {
  mockAIResponse,
  mockAnalytics,
  mockCompanyProfile,
  mockNotifications,
  mockPosts,
  mockStats
} from "@/lib/mockData";

const IS_STATIC = process.env.NEXT_PUBLIC_IS_STATIC === "true";

interface FullDashboardUIProps {
  title: string;
  subtitle: string;
}

type PlatformOption = "linkedin" | "twitter" | "instagram";

type CtaOption = "learn_more" | "book_demo" | "download";

export default function FullDashboardUI({ title, subtitle }: FullDashboardUIProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformOption>("linkedin");
  const [topic, setTopic] = useState("AI-powered social media pipeline");
  const [tone, setTone] = useState("Professional");
  const [cta, setCta] = useState<CtaOption>("learn_more");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generated, setGenerated] = useState("");
  const [version, setVersion] = useState(0);

  const stats = IS_STATIC ? mockStats : mockStats;
  const posts = IS_STATIC ? mockPosts : mockPosts;
  const analytics = IS_STATIC ? mockAnalytics : mockAnalytics;
  const notifications = IS_STATIC ? mockNotifications : mockNotifications;
  const profile = IS_STATIC ? mockCompanyProfile : mockCompanyProfile;

  const engagementMax = useMemo(() => {
    return Math.max(...analytics.weeklyData.map((item) => item.engagement));
  }, [analytics.weeklyData]);

  const generateMock = () => {
    setIsGenerating(true);
    window.setTimeout(() => {
      const source = selectedPlatform === "twitter" ? mockAIResponse.twitter : mockAIResponse.linkedin;
      const regenerated = version > 0 ? `${source}\n\nVariation ${version + 1}: angle refreshed for ${topic}.` : source;
      setGenerated(regenerated);
      setIsGenerating(false);
      toast.success("Mock content generated");
    }, 1500);
  };

  return (
    <main className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-3xl font-semibold text-slate-900">{title}</h1>
        <p className="text-sm text-slate-600">{subtitle}</p>
      </header>

      <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Total Posts</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.totalPosts}</p>
        </article>
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Scheduled</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.scheduledPosts}</p>
        </article>
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Published This Week</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.publishedThisWeek}</p>
        </article>
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Engagement Rate</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.engagementRate}</p>
        </article>
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Reach</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.reach}</p>
        </article>
        <article className="rounded-xl border bg-white p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">Impressions</p>
          <p className="mt-2 text-2xl font-semibold text-slate-900">{stats.impressions}</p>
        </article>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">AI Content Generation</h2>
          <p className="mt-1 text-sm text-slate-600">Generate preview content instantly in static mode.</p>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="text-slate-700">Platform</span>
              <select
                value={selectedPlatform}
                onChange={(event) => setSelectedPlatform(event.target.value as PlatformOption)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              >
                <option value="linkedin">LinkedIn</option>
                <option value="twitter">Twitter</option>
                <option value="instagram">Instagram</option>
              </select>
            </label>

            <label className="space-y-1 text-sm">
              <span className="text-slate-700">Tone</span>
              <select value={tone} onChange={(event) => setTone(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2">
                <option>Professional</option>
                <option>Confident</option>
                <option>Friendly</option>
              </select>
            </label>

            <label className="space-y-1 text-sm md:col-span-2">
              <span className="text-slate-700">Topic</span>
              <input
                value={topic}
                onChange={(event) => setTopic(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </label>

            <label className="space-y-1 text-sm">
              <span className="text-slate-700">CTA</span>
              <select value={cta} onChange={(event) => setCta(event.target.value as CtaOption)} className="w-full rounded-lg border border-slate-300 px-3 py-2">
                <option value="learn_more">Learn More</option>
                <option value="book_demo">Book Demo</option>
                <option value="download">Download</option>
              </select>
            </label>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={generateMock}
              disabled={isGenerating}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {isGenerating ? "Generating..." : "Generate"}
            </button>
            <button
              type="button"
              onClick={() => {
                setVersion((prev) => prev + 1);
                generateMock();
              }}
              disabled={isGenerating}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 disabled:opacity-60"
            >
              Regenerate
            </button>
          </div>

          {generated ? (
            <div className="mt-4 rounded-xl border bg-slate-50 p-4">
              <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Generated Content</p>
              <pre className="whitespace-pre-wrap text-sm text-slate-800">{generated}</pre>
              <button
                type="button"
                onClick={async () => {
                  await navigator.clipboard.writeText(generated);
                  toast.success("Copied to clipboard");
                }}
                className="mt-3 rounded-lg border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700"
              >
                Copy
              </button>
            </div>
          ) : null}
        </article>

        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>
          <ul className="mt-3 space-y-2">
            {notifications.map((item) => (
              <li key={item.id} className="rounded-lg border p-3">
                <p className="text-sm text-slate-800">{item.text}</p>
                <p className="mt-1 text-xs text-slate-500">{item.type} • {item.time}</p>
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Recent Posts</h2>
          <div className="mt-3 space-y-3">
            {posts.map((post) => (
              <div key={post.id} className="rounded-lg border p-3">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-wide text-slate-500">{post.platform}</p>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">{post.status}</span>
                </div>
                <p className="mt-2 text-sm text-slate-800">{post.content}</p>
                <p className="mt-2 text-xs text-slate-500">Scheduled: {post.scheduledFor ?? "Not scheduled"}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Likes {post.engagement.likes} • Comments {post.engagement.comments} • Shares {post.engagement.shares}
                </p>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Company Profile</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            <p><span className="font-medium">Name:</span> {profile.name}</p>
            <p><span className="font-medium">Platforms:</span> {profile.platforms.join(", ")}</p>
            <p><span className="font-medium">Posting Frequency:</span> LinkedIn {profile.postingFrequency.linkedin}/wk, Twitter {profile.postingFrequency.twitter}/wk, Instagram {profile.postingFrequency.instagram}/wk</p>
            <p><span className="font-medium">CTA Types:</span> {profile.ctaTypes.join(", ")}</p>
            <p><span className="font-medium">Brand Colors:</span> {profile.brandColors.join(", ")}</p>
            <p><span className="font-medium">Approved Vocabulary:</span> {profile.approvedVocabulary.join(", ")}</p>
            <p><span className="font-medium">Banned Vocabulary:</span> {profile.bannedVocabulary.join(", ")}</p>
          </div>
        </article>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Weekly Performance</h2>
          <div className="mt-3 space-y-2">
            {analytics.weeklyData.map((item) => (
              <div key={item.day}>
                <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
                  <span>{item.day}</span>
                  <span>Posts {item.posts} • Engagement {item.engagement}</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-teal-600"
                    style={{ width: `${Math.round((item.engagement / engagementMax) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="rounded-xl border bg-white p-5">
          <h2 className="text-lg font-semibold text-slate-900">Platform Breakdown</h2>
          <div className="mt-3 space-y-3">
            {analytics.platformBreakdown.map((item) => (
              <div key={item.platform}>
                <div className="mb-1 flex items-center justify-between text-sm text-slate-700">
                  <span>{item.platform}</span>
                  <span>{item.percentage}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div className="h-2 rounded-full" style={{ width: `${item.percentage}%`, backgroundColor: item.color }} />
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
