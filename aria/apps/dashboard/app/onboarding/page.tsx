"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { z } from "zod";
import { apiPost } from "../../lib/client";

const ResponseSchema = z.object({ company_id: z.string(), profile_version: z.number(), status: z.string() });

export default function OnboardingPage() {
  const [result, setResult] = useState<string>("");

  const mutation = useMutation({
    mutationFn: async () =>
      apiPost(
        "/v1/onboarding/company-profile",
        {
          company_name: "ARIA Demo Co",
          industry_vertical: "SaaS",
          target_market: { regions: ["US"], segments: ["B2B"], persona_summary: "Marketing leaders" },
          brand_positioning_statement: "We help teams run highly intelligent campaigns that scale predictably.",
          tone_of_voice_descriptors: ["clear", "confident"],
          competitor_list: ["Competitor A"],
          platform_presence: { instagram: true, linkedin: true, facebook: false, x: true, tiktok: false, pinterest: false },
          posting_frequency_goal: { instagram: 3, linkedin: 4, facebook: 0, x: 5, tiktok: 0, pinterest: 0 },
          primary_cta_types: ["signup"],
          brand_color_hex_codes: ["#165D52"],
          approved_vocabulary_list: ["insightful"],
          banned_vocabulary_list: ["cheap"],
          sample_post_images: []
        },
        ResponseSchema
      )
  });

  return (
    <section className="space-y-4 rounded-2xl border border-ink/15 bg-white/70 p-6">
      <h2 className="font-display text-3xl">Onboarding</h2>
      <button className="rounded-xl bg-accent px-4 py-2 font-semibold text-white" onClick={() => mutation.mutate()}>
        Submit Demo Onboarding Payload
      </button>
      {mutation.isSuccess && <pre className="text-sm">{JSON.stringify(mutation.data, null, 2)}</pre>}
      {mutation.isError && <p className="text-red-700">{String(mutation.error)}</p>}
      {result && <p>{result}</p>}
    </section>
  );
}
