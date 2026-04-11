// filename: config/constants.ts
// purpose: Immutable UI constants aligned with backend and decision engine contracts.
// dependencies: types

import type { Platform } from "@/types";

export const PLATFORM_CHAR_LIMITS = {
  instagram: 2200,
  linkedin: 3000,
  facebook: 63206,
  x: 280,
  tiktok: 2200,
  pinterest: 500
} as const satisfies Record<Platform, number>;

export const PLATFORM_HASHTAG_CAPS = {
  instagram: 20,
  linkedin: 5,
  x: 3,
  tiktok: 8,
  pinterest: 10,
  facebook: 5
} as const satisfies Record<Platform, number>;

export const PLATFORM_COOLDOWN_MINUTES = {
  instagram: 360,
  linkedin: 720,
  facebook: 360,
  x: 60,
  tiktok: 480,
  pinterest: 240
} as const satisfies Record<Platform, number>;

export const RETRY_SCHEDULE_SECONDS = [60, 300, 900, 2700, 7200] as const;

export const RETRY_JITTER_PERCENT = 0.2 as const;

export const VARIANT_COMPLIANCE_THRESHOLD = 0.9 as const;

export const AUDIENCE_CONFIDENCE_THRESHOLDS = {
  high: 0.75,
  medium: 0.55
} as const;

export const ONBOARDING_PASS_THRESHOLD = 70 as const;

export const REASON_CODE_LABELS = {
  historical_win: "Past winner",
  industry_baseline: "Industry norm",
  low_competitor_density: "Low competition"
} as const;

export const POSTING_FREQUENCY_LIMITS = {
  instagram: 21,
  linkedin: 14,
  facebook: 21,
  x: 70,
  tiktok: 21,
  pinterest: 35
} as const satisfies Record<Platform, number>;

export const QUALITY_SCORE_THRESHOLDS = {
  good: 60,
  warning: 40
} as const;
