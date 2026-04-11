// filename: components/audience/AudienceConfidenceBadge.tsx
// purpose: Confidence indicator using backend thresholds.
// dependencies: config/constants

"use client";

import { AUDIENCE_CONFIDENCE_THRESHOLDS } from "@/config/constants";

interface Props {
  confidence: number;
}

export const AudienceConfidenceBadge = ({ confidence }: Props) => {
  if (confidence >= AUDIENCE_CONFIDENCE_THRESHOLDS.high) {
    return <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-700">High confidence</span>;
  }
  if (confidence >= AUDIENCE_CONFIDENCE_THRESHOLDS.medium) {
    return (
      <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800">
        Medium - review recommended
      </span>
    );
  }
  return <span className="rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">Low - approval required</span>;
};
