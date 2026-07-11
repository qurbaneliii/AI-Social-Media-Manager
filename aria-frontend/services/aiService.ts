import { IS_STATIC } from "@/lib/isStatic";
import {
  PREVIEW_MODE_MESSAGE,
  mockGeneratedContent
} from "@/lib/mockData";
import {
  generateContentPackage,
  recommendHashtags,
  refineContent,
  researchTrends,
  reviewContentQuality,
  type BrandProfile,
  type ContentRequest,
  type GeneratedContentPackage,
  type PlatformContext
} from "@/lib/api/ai-workspace";

export type AIPlatform = "linkedin" | "twitter" | "instagram" | "facebook" | "tiktok" | "pinterest" | "x";

export type AICtaType = "learn_more" | "book_demo" | "buy_now" | "download" | "comment" | "share";

export interface AIGenerateContentRequest {
  platform: AIPlatform;
  topic: string;
  tone: string;
  ctaType: AICtaType;
  brandColors: string[];
  approvedVocabulary: string[];
  bannedVocabulary: string[];
  postingFrequency?: number;
  companyProfile?: Record<string, unknown>;
}

export interface AIGenerateContentResponse {
  content: string;
  platform: Exclude<AIPlatform, "x">;
}

export interface AIGenerateBatchResult {
  success: boolean;
  platform: Exclude<AIPlatform, "x">;
  content?: string;
  error?: string;
}

export interface AIGenerateBatchResponse {
  results: AIGenerateBatchResult[];
}

export interface AIImproveContentRequest {
  content: string;
  instruction: string;
}

export interface AIImproveContentResponse {
  improved: string;
}

export interface AIAnalyzeContentRequest {
  content: string;
  platform: AIPlatform;
}

export interface AIAnalyzeContentResponse {
  scores: {
    engagement: number;
    clarity: number;
    cta_strength: number;
  };
  suggestions: string[];
}

export interface AISuggestHashtagsRequest {
  content: string;
  platform: AIPlatform;
}

export interface AISuggestHashtagsResponse {
  hashtags: string[];
}

export interface AISuggestTopicsRequest {
  industry: string;
  platforms: AIPlatform[];
  companyProfile: Record<string, unknown>;
}

export interface AISuggestTopicsResponse {
  topics: string[];
}

const normalizePlatform = (platform: AIPlatform): Exclude<AIPlatform, "x"> => {
  return platform === "x" ? "twitter" : platform;
};

const isPreviewMode = (): boolean => {
  if (IS_STATIC) {
    return true;
  }
  if (typeof window === "undefined") {
    return false;
  }
  return localStorage.getItem("isPreview") === "true";
};

const stringValue = (input: unknown, fallback = ""): string => {
  return typeof input === "string" && input.trim() ? input.trim() : fallback;
};

const stringArray = (input: unknown, fallback: string[] = []): string[] => {
  return Array.isArray(input) ? input.map((item) => String(item).trim()).filter(Boolean) : fallback;
};

const buildBrandProfile = (params: AIGenerateContentRequest): BrandProfile => {
  const companyProfile = params.companyProfile ?? {};
  const companyId = stringValue(companyProfile.companyId, "selected-brand");
  const companyName = stringValue(companyProfile.companyName, stringValue(companyProfile.name, "Selected brand"));
  const tone = params.tone
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const selectedPlatform = normalizePlatform(params.platform);

  return {
    brand_id: companyId,
    brand_name: companyName,
    industry: stringValue(companyProfile.industry, "social media"),
    description: stringValue(companyProfile.description, "Brand profile selected in ARIA Create workflow."),
    products_or_services: stringArray(companyProfile.productsOrServices, ["social media content"]),
    target_audience: stringArray(companyProfile.targetAudience, ["selected audience"]),
    tone_of_voice: tone.length ? tone : stringArray(companyProfile.tone, ["professional"]),
    brand_values: stringArray(companyProfile.brandValues, ["approval-based publishing"]),
    forbidden_topics: stringArray(companyProfile.forbiddenTopics),
    forbidden_words: params.bannedVocabulary,
    approved_claims: params.approvedVocabulary,
    competitors: stringArray(companyProfile.competitors),
    platforms: [selectedPlatform],
    visual_style: { brand_colors: params.brandColors },
    business_goals: [params.topic],
    language_preferences: ["en"]
  };
};

const buildPlatformContext = (params: AIGenerateContentRequest): PlatformContext => ({
  platform: normalizePlatform(params.platform),
  content_type: "post",
  objective: params.ctaType,
  tone_override: params.tone,
  hashtag_limit: 12,
  format_rules: params.postingFrequency ? [`posting_frequency:${params.postingFrequency}`] : []
});

const buildContentRequest = (params: AIGenerateContentRequest): ContentRequest => ({
  brand_profile: buildBrandProfile(params),
  platform_context: buildPlatformContext(params),
  campaign_objective: params.ctaType,
  topic: params.topic,
  content_pillar: "create",
  number_of_variants: 1,
  extra_context: {
    approved_vocabulary: params.approvedVocabulary,
    banned_vocabulary: params.bannedVocabulary,
    brand_colors: params.brandColors
  }
});

const packageToContent = (pkg: GeneratedContentPackage): string => {
  return [pkg.hook, pkg.caption, pkg.cta].filter(Boolean).join("\n\n");
};

const packageFromDraft = (content: string, platform: AIPlatform): GeneratedContentPackage => ({
  platform: normalizePlatform(platform),
  content_type: "post",
  hook: content.split("\n")[0] ?? content,
  caption: content,
  cta: "",
  hashtags: [],
  visual_brief: {},
  video_script: null,
  carousel_structure: [],
  posting_recommendation: {},
  rationale: "Draft supplied by the user for quality review.",
  risks: []
});

export const generateContent = async (
  params: AIGenerateContentRequest
): Promise<AIGenerateContentResponse> => {
  if (isPreviewMode()) {
    const platform = normalizePlatform(params.platform);
    const content =
      platform === "linkedin"
        ? mockGeneratedContent.linkedin
        : platform === "twitter"
          ? mockGeneratedContent.twitter
          : `Preview mode content for ${platform}. ${PREVIEW_MODE_MESSAGE}`;

    return {
      content,
      platform
    };
  }

  const generated = await generateContentPackage(buildContentRequest(params));
  return {
    content: packageToContent(generated),
    platform: normalizePlatform(params.platform)
  };
};

export const generateBatch = async (
  params: AIGenerateContentRequest[]
): Promise<AIGenerateBatchResponse> => {
  if (isPreviewMode()) {
    return {
      results: params.map((item) => {
        const platform = normalizePlatform(item.platform);
        const content =
          platform === "linkedin"
            ? mockGeneratedContent.linkedin
            : platform === "twitter"
              ? mockGeneratedContent.twitter
              : `Preview mode content for ${platform}. ${PREVIEW_MODE_MESSAGE}`;

        return {
          success: true,
          platform,
          content
        };
      })
    };
  }

  const results = await Promise.all(
    params.map(async (item) => {
      try {
        const generated = await generateContent(item);
        return {
          success: true,
          platform: generated.platform,
          content: generated.content
        };
      } catch (error) {
        return {
          success: false,
          platform: normalizePlatform(item.platform),
          error: error instanceof Error ? error.message : "Generation failed"
        };
      }
    })
  );
  return { results };
};

export const improveContent = async (
  params: AIImproveContentRequest
): Promise<AIImproveContentResponse> => {
  if (isPreviewMode()) {
    return {
      improved: `${params.content}\n\n[Preview improvement] ${PREVIEW_MODE_MESSAGE}`
    };
  }

  return refineContent(params);
};

export const analyzeContent = async (
  params: AIAnalyzeContentRequest
): Promise<AIAnalyzeContentResponse> => {
  if (isPreviewMode()) {
    return {
      scores: {
        engagement: 72,
        clarity: 78,
        cta_strength: 69
      },
      suggestions: [
        "Lead with a stronger hook in the first sentence.",
        "Tighten wording to improve readability.",
        "End with a clearer CTA for better conversion."
      ]
    };
  }

  const request = buildContentRequest({
    platform: params.platform,
    topic: params.content,
    tone: "professional",
    ctaType: "learn_more",
    brandColors: [],
    approvedVocabulary: [],
    bannedVocabulary: [],
    companyProfile: { companyName: "Selected brand" }
  });
  const review = await reviewContentQuality({
    request,
    package: packageFromDraft(params.content, params.platform)
  });
  return {
    scores: {
      engagement: Math.round(review.engagement_potential_score * 100),
      clarity: Math.round(review.clarity_score * 100),
      cta_strength: Math.round(review.cta_strength_score * 100)
    },
    suggestions: review.improvement_notes
  };
};

export const suggestHashtags = async (
  params: AISuggestHashtagsRequest
): Promise<AISuggestHashtagsResponse> => {
  if (isPreviewMode()) {
    return {
      hashtags: ["AriaConsole", "SocialMedia", "ContentStrategy", "PreviewMode"]
    };
  }

  const request = buildContentRequest({
    platform: params.platform,
    topic: params.content,
    tone: "professional",
    ctaType: "learn_more",
    brandColors: [],
    approvedVocabulary: [],
    bannedVocabulary: [],
    companyProfile: { companyName: "Selected brand" }
  });
  const response = await recommendHashtags({
    brand_profile: request.brand_profile,
    platform_context: request.platform_context,
    topic: params.content,
    trend_keywords: params.content
      .split(/\s+/)
      .map((item) => item.replace(/[^a-z0-9#]/gi, ""))
      .filter(Boolean)
      .slice(0, 8),
    max_hashtags: 12
  });
  return {
    hashtags: [
      ...response.branded_hashtags,
      ...response.campaign_hashtags,
      ...response.niche_hashtags,
      ...response.broad_hashtags,
      ...response.trend_based_hashtags
    ].slice(0, 12)
  };
};

export const suggestTopics = async (
  params: AISuggestTopicsRequest
): Promise<AISuggestTopicsResponse> => {
  if (isPreviewMode()) {
    return {
      topics: [
        `Top ${params.industry} trends this quarter`,
        "Behind the scenes: our workflow for campaign quality",
        "5 mistakes brands make in social messaging",
        "How to adapt one idea across multiple platforms",
        "What measurable CTA performance looks like"
      ]
    };
  }

  const brandProfile: BrandProfile = {
    brand_id: stringValue(params.companyProfile.companyId, "selected-brand"),
    brand_name: stringValue(params.companyProfile.companyName, stringValue(params.companyProfile.name, "Selected brand")),
    industry: params.industry,
    description: "Topic suggestion request from ARIA Create workflow.",
    products_or_services: ["social media content"],
    target_audience: ["selected audience"],
    tone_of_voice: stringArray(params.companyProfile.tone, ["professional"]),
    brand_values: ["approval-based publishing"],
    forbidden_topics: [],
    forbidden_words: [],
    approved_claims: [],
    competitors: [],
    platforms: params.platforms.map(normalizePlatform),
    visual_style: {},
    business_goals: [`Create relevant ${params.industry} social posts`],
    language_preferences: ["en"]
  };
  const response = await researchTrends({
    brand_profile: brandProfile,
    trends: [
      {
        keyword: params.industry,
        source: "create_workflow",
        signals: params.companyProfile
      }
    ],
    platforms: params.platforms.map(normalizePlatform),
    business_goal: `Suggest topics for ${params.industry}`
  });
  const topics = [...response.relevant_topics, ...response.trend_opportunities].filter(Boolean);
  return {
    topics: topics.length ? topics.slice(0, 8) : [`${params.industry} content strategy`, `${params.industry} customer questions`]
  };
};
