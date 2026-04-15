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

const toApiUrl = (path: string): string => `/api${path}`;

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
  return postJson<AIGenerateContentResponse>("/ai/generate-content", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
};

export const generateBatch = async (
  params: AIGenerateContentRequest[]
): Promise<AIGenerateBatchResponse> => {
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
  return postJson<AIImproveContentResponse>("/ai/improve-content", params);
};

export const analyzeContent = async (
  params: AIAnalyzeContentRequest
): Promise<AIAnalyzeContentResponse> => {
  return postJson<AIAnalyzeContentResponse>("/ai/analyze-content", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
};

export const suggestHashtags = async (
  params: AISuggestHashtagsRequest
): Promise<AISuggestHashtagsResponse> => {
  return postJson<AISuggestHashtagsResponse>("/ai/suggest-hashtags", {
    ...params,
    platform: normalizePlatform(params.platform)
  });
};

export const suggestTopics = async (
  params: AISuggestTopicsRequest
): Promise<AISuggestTopicsResponse> => {
  return postJson<AISuggestTopicsResponse>("/ai/suggest-topics", {
    ...params,
    platforms: params.platforms.map(normalizePlatform)
  });
};
