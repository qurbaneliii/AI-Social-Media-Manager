"use client";

import { useMemo, useState } from "react";

import { PostCard } from "@/components/dashboard/PostCard";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useDashboard } from "@/hooks/useDashboard";
import type { PostStatus } from "@/lib/mock-data";

export default function PostsPage() {
  const { posts } = useDashboard();
  const [status, setStatus] = useState<PostStatus | "all">("all");

  const filtered = useMemo(() => (status === "all" ? posts : posts.filter((post) => post.status === status)), [posts, status]);

  return (
    <div className="space-y-6">
      <div>
        <h1>Posts</h1>
        <p className="text-sm text-[var(--text-secondary)]">Manage scheduled, draft, and published content in one queue.</p>
      </div>

      <Tabs value={status} onValueChange={(value) => setStatus(value as PostStatus | "all")}> 
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          <TabsTrigger value="published">Published</TabsTrigger>
          <TabsTrigger value="draft">Draft</TabsTrigger>
          <TabsTrigger value="failed">Failed</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((post) => (
          <PostCard key={post.id} {...post} />
        ))}
      </div>
    </div>
  );
}
