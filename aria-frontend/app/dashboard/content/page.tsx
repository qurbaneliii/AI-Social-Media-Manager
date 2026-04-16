"use client";

import { AIGeneratorPanel } from "@/components/dashboard/AIGeneratorPanel";
import { PostCard } from "@/components/dashboard/PostCard";
import { useDashboard } from "@/hooks/useDashboard";

export default function ContentDashboardPage() {
  const { posts } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1>Content Dashboard</h1>
        <p className="text-sm text-[var(--text-secondary)]">Draft, iterate, and optimize social content with AI assistance.</p>
      </div>

      <AIGeneratorPanel />

      <section className="space-y-3">
        <h2>Drafts and Recent Posts</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {posts.map((post) => (
            <PostCard key={post.id} {...post} />
          ))}
        </div>
      </section>
    </div>
  );
}
