// filename: components/ui/QualityScoreGauge.tsx
// purpose: Circular gauge for quality score visualization.

"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { QUALITY_SCORE_THRESHOLDS } from "@/config/constants";
import type { ContentQualityScore } from "@/types";

interface Props {
  score: ContentQualityScore;
}

export const QualityScoreGauge = ({ score }: Props) => {
  const value = Math.max(0, Math.min(100, score.overall));
  const r = 44;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;

  const subscoreData = [
    { key: "engagement_prediction", value: score.subscores.engagement_prediction },
    { key: "tone_match", value: score.subscores.tone_match },
    { key: "platform_compliance", value: score.subscores.platform_compliance },
    { key: "keyword_coverage", value: score.subscores.keyword_coverage },
    { key: "cta_strength", value: score.subscores.cta_strength }
  ];

  const getColor = (v: number) => {
    if (v < QUALITY_SCORE_THRESHOLDS.warning) return "#dc2626";
    if (v < QUALITY_SCORE_THRESHOLDS.good) return "#d97706";
    return "#059669";
  };

  return (
    <div className="space-y-4 rounded-xl border bg-white p-3">
      <div className="inline-flex items-center gap-3">
        <svg width="110" height="110" viewBox="0 0 110 110" role="img" aria-label={`Quality score ${Math.round(value)}`}>
          <circle cx="55" cy="55" r={r} fill="none" stroke="#e2e8f0" strokeWidth="12" />
          <circle
            cx="55"
            cy="55"
            r={r}
            fill="none"
            stroke={getColor(value)}
            strokeWidth="12"
            strokeDasharray={c}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 55 55)"
          />
          <text x="55" y="61" textAnchor="middle" fontSize="20" fontWeight="700" fill="#0f172a">
            {Math.round(value)}
          </text>
        </svg>
        <div>
          <p className="text-sm font-semibold text-slate-800">Quality score</p>
          <p className="text-xs text-slate-500">Predictive ranking confidence</p>
        </div>
      </div>

      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={subscoreData} layout="vertical" margin={{ left: 24 }}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis dataKey="key" type="category" width={130} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" radius={[4, 4, 4, 4]}>
              {subscoreData.map((entry) => (
                <Cell key={entry.key} fill={getColor(entry.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
