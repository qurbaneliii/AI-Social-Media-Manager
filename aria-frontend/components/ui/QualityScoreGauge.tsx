// filename: components/ui/QualityScoreGauge.tsx
// purpose: Circular gauge for quality score visualization.

"use client";

interface Props {
  score: number;
}

export const QualityScoreGauge = ({ score }: Props) => {
  const value = Math.max(0, Math.min(100, score));
  const r = 44;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;

  return (
    <div className="inline-flex items-center gap-3 rounded-xl border bg-white p-3">
      <svg width="110" height="110" viewBox="0 0 110 110" role="img" aria-label={`Quality score ${Math.round(value)}`}>
        <circle cx="55" cy="55" r={r} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle
          cx="55"
          cy="55"
          r={r}
          fill="none"
          stroke="#0284c7"
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
  );
};
