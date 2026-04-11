"use client";

import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { apiPost } from "../../lib/client";

const GenerateSchema = z.object({ post_id: z.string(), status: z.string(), estimated_ready_seconds: z.number() });

export default function GeneratePage() {
  const mutation = useMutation({
    mutationFn: async () =>
      apiPost(
        "/v1/posts/generate",
        {
          company_id: "00000000-0000-0000-0000-000000000001",
          post_intent: "announce",
          core_message: "We are launching ARIA to automate social strategy and publishing outcomes.",
          target_platforms: ["linkedin", "x"],
          campaign_tag: "spring_launch",
          manual_keywords: ["ai", "social"],
          urgency_level: "scheduled"
        },
        GenerateSchema
      )
  });

  return (
    <section className="space-y-4 rounded-2xl border border-ink/15 bg-white/70 p-6">
      <h2 className="font-display text-3xl">Post Generation</h2>
      <button className="rounded-xl bg-accent px-4 py-2 font-semibold text-white" onClick={() => mutation.mutate()}>
        Generate Post Package
      </button>
      {mutation.isSuccess && <pre className="text-sm">{JSON.stringify(mutation.data, null, 2)}</pre>}
      {mutation.isError && <p className="text-red-700">{String(mutation.error)}</p>}
    </section>
  );
}
