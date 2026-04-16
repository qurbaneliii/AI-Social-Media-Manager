import { IS_STATIC } from "@/lib/isStatic";
import {
  PREVIEW_MODE_MESSAGE,
  mockGeneratedContent
} from "@/lib/mockData";

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

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");

const normalizePlatform = (platform: AIPlatform): Exclude<AIPlatform, "x"> => {
  return platform === "x" ? "twitter" : platform;
};

const getTokenFromStorage = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }

  return (
    localStorage.getItem("aria_token") ??
    sessionStorage.getItem("aria_token") ??
    localStorage.getItem("auth_token") ??
    sessionStorage.getItem("auth_token")
  );
};

const getTokenFromCookie = (): string | null => {
  if (typeof document === "undefined") {
    return null;
  }

  const match = document.cookie.match(/(?:^|; )auth_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
};

const getAuthToken = (): string | null => {
  return getTokenFromStorage() ?? getTokenFromCookie();
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

const toApiUrl = (path: string): string => {
  if (!API_BASE) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured");
  }
  return `${API_BASE}${path}`;
};

const postJson = async <TResponse>(path: string, body: unknown): Promise<TResponse> => {
  const token = getAuthToken();

  const response = await fetch(toApiUrl(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    credentials: "include",
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = (await response.json()) as { error?: string; message?: string };
      message = payload.error ?? payload.message ?? message;
    } catch {
      // Keep fallback message.
    }

    throw new Error(message);
  }

  return (await response.json()) as TResponse;
};

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

  return postJson<AIGenerateContentResponse>("/ai/generate-content", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
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

  return postJson<AIGenerateBatchResponse>(
    "/ai/generate-batch",
    params.map((item) => ({
      ...item,
      platform: normalizePlatform(item.platform)
    }))
  );
};

export const improveContent = async (
  params: AIImproveContentRequest
): Promise<AIImproveContentResponse> => {
  if (isPreviewMode()) {
    return {
      improved: `${params.content}\n\n[Preview improvement] ${PREVIEW_MODE_MESSAGE}`
    };
  }

  return postJson<AIImproveContentResponse>("/ai/improve-content", params);
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

  return postJson<AIAnalyzeContentResponse>("/ai/analyze-content", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
};

export const suggestHashtags = async (
  params: AISuggestHashtagsRequest
): Promise<AISuggestHashtagsResponse> => {
  if (isPreviewMode()) {
    return {
      hashtags: ["AriaConsole", "SocialMedia", "ContentStrategy", "PreviewMode"]
    };
  }

  return postJson<AISuggestHashtagsResponse>("/ai/suggest-hashtags", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
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

  return postJson<AISuggestTopicsResponse>("/ai/suggest-topics", {
    ...params,
    platforms: params.platforms.map(normalizePlatform)
  });
};
