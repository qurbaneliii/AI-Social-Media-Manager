// filename: components/brand/ToneFingerprintDisplay.tsx
// purpose: Render brand tone values and key vocabulary chips.

"use client";

import type { ToneFingerprint } from "@/types";

interface Props {
  tone: ToneFingerprint;
  preferred: string[];
  avoid: string[];
}

const AxisBar = ({ label, value }: { label: string; value: number }) => (
  <div>
    <div className="mb-1 flex items-center justify-between text-xs text-slate-600">
      <span>{label}</span>
      <span>{Math.round(value * 100)}%</span>
    </div>
    <div className="h-2 rounded-full bg-slate-200">
      <div className="h-2 rounded-full bg-sky-600" style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }} />
    </div>
  </div>
);

export const ToneFingerprintDisplay = ({ tone, preferred, avoid }: Props) => {
  return (
    <div className="space-y-4 rounded-xl border bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-800">Tone fingerprint</h3>
      <div className="grid gap-3 md:grid-cols-2">
        <AxisBar label="Formality" value={tone.formality_score} />
        <AxisBar label="Humor" value={tone.humor_score} />
        <AxisBar label="Assertiveness" value={tone.assertiveness_score} />
        <AxisBar label="Optimism" value={tone.optimism_score} />
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Preferred</p>
        <div className="flex flex-wrap gap-2">
          {preferred.map((word) => (
            <span key={word} className="rounded-full bg-emerald-50 px-3 py-1 text-xs text-emerald-700">
              {word}
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Avoid</p>
        <div className="flex flex-wrap gap-2">
          {avoid.map((word) => (
            <span key={word} className="rounded-full bg-red-50 px-3 py-1 text-xs text-red-700">
              {word}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
