// filename: components/hashtags/HashtagTierDisplay.tsx
// purpose: Three-tier hashtag visualization with platform cap behavior.
// dependencies: config/constants, types

"use client";

import { PLATFORM_HASHTAG_CAPS } from "@/config/constants";
import type { HashtagSet, Platform } from "@/types";

interface Props {
  hashtagSet: HashtagSet;
  activePlatform: Platform;
  platformCap?: number;
  onToggle?: (tag: string) => void;
}

export const HashtagTierDisplay = ({ hashtagSet, activePlatform, platformCap, onToggle }: Props) => {
  const cap = platformCap ?? PLATFORM_HASHTAG_CAPS[activePlatform];

  const columns = [
    { title: "Broad", items: hashtagSet.broad },
    { title: "Niche", items: hashtagSet.niche },
    { title: "Micro", items: hashtagSet.micro }
  ] as const;

  const total = hashtagSet.broad.length + hashtagSet.niche.length + hashtagSet.micro.length;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {columns.map((column, columnIndex) => {
          const prefixCount = columns.slice(0, columnIndex).reduce((acc, item) => acc + item.items.length, 0);

          return (
          <section key={column.title} className="rounded-xl border bg-white p-3">
            <header className="mb-3 text-sm font-semibold text-slate-700">
              {column.title} ({Math.min(column.items.length, cap)}/{cap} max)
            </header>
            <div className="space-y-2">
              {column.items.map((item, idx) => {
                const globalIndex = prefixCount + idx;
                const overCap = globalIndex >= cap;
                return (
                  <button
                    key={`${column.title}-${item.tag}-${idx}`}
                    type="button"
                    onClick={() => onToggle?.(item.tag)}
                    className={`w-full rounded-lg border p-2 text-left ${overCap ? "opacity-40" : ""}`}
                    title={overCap ? `Cap reached for ${activePlatform}` : item.tag}
                  >
                    <div className="mb-1 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-800">
                      #{item.tag}
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-slate-200">
                      <div className="h-1.5 rounded-full bg-teal-600" style={{ width: `${Math.max(0, Math.min(100, item.score * 100))}%` }} />
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
          );
        })}
      </div>
      <p className="text-sm text-slate-600">{total} tags selected (cap: {cap})</p>
    </div>
  );
};
