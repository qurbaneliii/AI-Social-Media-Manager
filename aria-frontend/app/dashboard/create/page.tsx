"use client";

import { AIGeneratorPanel } from "@/components/dashboard/AIGeneratorPanel";

export default function CreatePostPage() {
  return (
    <div className="space-y-5">
      <div>
        <h1>Create Post</h1>
        <p className="text-sm text-[var(--text-secondary)]">Generate and refine platform-specific posts before scheduling.</p>
      </div>
      <AIGeneratorPanel />
    </div>
  );
}
