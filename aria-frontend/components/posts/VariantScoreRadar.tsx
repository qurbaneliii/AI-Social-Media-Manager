// filename: components/posts/VariantScoreRadar.tsx
// purpose: Radar chart for variant score dimensions.
// dependencies: recharts, types

"use client";

import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

import type { PostVariant } from "@/types";

interface Props {
  scores: PostVariant["scores"];
}

export const VariantScoreRadar = ({ scores }: Props) => {
  const data = [
    { key: "Engagement", value: scores.engagement_predicted },
    { key: "Tone match", value: scores.tone_match },
    { key: "CTA", value: scores.cta_presence },
    { key: "Keywords", value: scores.keyword_inclusion },
    { key: "Compliance", value: scores.platform_compliance }
  ];

  return (
    <div className="h-[280px] w-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius={95}>
          <PolarGrid radialLines />
          <PolarAngleAxis dataKey="key" tick={{ fontSize: 12 }} />
          <Radar dataKey="value" stroke="#0d9488" fill="#0d9488" fillOpacity={0.6} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
};
