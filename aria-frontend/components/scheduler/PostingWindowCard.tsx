// filename: components/scheduler/PostingWindowCard.tsx
// purpose: Selectable posting window card with confidence and reason labels.
// dependencies: config/constants, types

"use client";

import { PLATFORM_COOLDOWN_MINUTES, REASON_CODE_LABELS } from "@/config/constants";
import type { Platform, PostingWindow } from "@/types";

interface Props {
  window: PostingWindow;
  platform: Platform;
  selected: boolean;
  onSelect: () => void;
}

export const PostingWindowCard = ({ window, platform, selected, onSelect }: Props) => {
  const cooldownHours = PLATFORM_COOLDOWN_MINUTES[platform] / 60;

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-xl border bg-white p-3 text-left ${selected ? "ring-2 ring-teal-600" : ""}`}
    >
      <div className="text-sm font-semibold text-slate-900">{new Date(window.start_local).toLocaleString()}</div>
      <div className="mt-2 h-2 rounded-full bg-slate-200">
        <div className="h-2 rounded-full bg-teal-600" style={{ width: `${Math.max(0, Math.min(100, window.confidence * 100))}%` }} />
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {window.reason_codes.map((code) => (
          <span
            key={code}
            className={`rounded px-2 py-0.5 text-xs ${
              code === "historical_win"
                ? "bg-emerald-100 text-emerald-700"
                : code === "industry_baseline"
                  ? "bg-sky-100 text-sky-700"
                  : "bg-teal-100 text-teal-700"
            }`}
          >
            {REASON_CODE_LABELS[code]}
          </span>
        ))}
      </div>
      <p className="mt-2 text-xs text-slate-500">Min gap: {cooldownHours}h</p>
    </button>
  );
};
