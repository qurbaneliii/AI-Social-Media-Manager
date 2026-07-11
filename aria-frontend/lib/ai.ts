import type { DashboardPlatform } from "@/lib/mock-data";
import {
  defaultBrandProfile,
  generateContentPackage,
  type BrandProfile,
  type PlatformContext
} from "@/lib/api/ai-workspace";

export interface GeneratePayload {
  platform: DashboardPlatform;
  tone: string;
  topic: string;
  cta: string;
  context?: string;
  brandVocab?: {
    approved: string[];
    banned: string[];
    brandName?: string;
  };
}

interface StreamHandlers {
  onChunk: (chunk: string) => void;
  signal?: AbortSignal;
}

export const streamGeneratedContent = async (payload: GeneratePayload, handlers: StreamHandlers): Promise<void> => {
  if (handlers.signal?.aborted) {
    throw new DOMException("Generation aborted", "AbortError");
  }

  const brandProfile: BrandProfile = {
    ...defaultBrandProfile,
    brand_name: payload.brandVocab?.brandName ?? defaultBrandProfile.brand_name,
    forbidden_words: payload.brandVocab?.banned ?? defaultBrandProfile.forbidden_words,
    approved_claims: payload.brandVocab?.approved?.length
      ? payload.brandVocab.approved
      : defaultBrandProfile.approved_claims
  };
  const platformContext: PlatformContext = {
    platform: payload.platform,
    content_type: "social_post",
    objective: payload.cta,
    tone_override: payload.tone
  };

  const result = await generateContentPackage({
    brand_profile: brandProfile,
    platform_context: platformContext,
    campaign_objective: payload.cta,
    topic: payload.topic,
    content_pillar: payload.context ?? "general campaign content",
    number_of_variants: 1,
    extra_context: {
      source: "legacy-dashboard-generator"
    }
  });

  if (handlers.signal?.aborted) {
    throw new DOMException("Generation aborted", "AbortError");
  }

  handlers.onChunk(result.caption);
};
