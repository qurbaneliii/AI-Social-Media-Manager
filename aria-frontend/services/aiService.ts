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

const parseIntegerEnv = (raw: string | undefined, fallback: number, minimum: number): number => {
  if (!raw) {
    return fallback;
  }

  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed)) {
    return fallback;
  }

  return Math.max(minimum, parsed);
};

const AI_REQUEST_TIMEOUT_MS = parseIntegerEnv(process.env.NEXT_PUBLIC_AI_REQUEST_TIMEOUT_MS, 45000, 1000);
const AI_REQUEST_RETRIES = parseIntegerEnv(process.env.NEXT_PUBLIC_AI_REQUEST_RETRIES, 2, 0);
const RETRYABLE_STATUS = new Set([408, 409, 425, 429, 500, 502, 503, 504]);

const sleep = async (ms: number): Promise<void> => {
  await new Promise((resolve) => setTimeout(resolve, ms));
};

const shouldRetryStatus = (status: number): boolean => {
  return RETRYABLE_STATUS.has(status);
};

const extractErrorMessage = async (response: Response): Promise<string> => {
  let message = `Request failed with status ${response.status}`;

  try {
    const payload = (await response.json()) as { error?: string; message?: string; detail?: unknown };
    const detailMessage = typeof payload.detail === "string" ? payload.detail : undefined;
    message = payload.error ?? payload.message ?? detailMessage ?? message;
  } catch {
    // Keep fallback message.
  }

  return message;
};

const postJson = async <TResponse>(path: string, body: unknown): Promise<TResponse> => {
  const token = getAuthToken();

  let attempt = 0;
  for (;;) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), AI_REQUEST_TIMEOUT_MS);

    try {
      const response = await fetch(toApiUrl(path), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: "include",
        body: JSON.stringify(body),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        return (await response.json()) as TResponse;
      }

      const message = await extractErrorMessage(response);
      if (attempt < AI_REQUEST_RETRIES && shouldRetryStatus(response.status)) {
        const delay = Math.min(1000 * (2 ** attempt), 5000);
        await sleep(delay);
        attempt += 1;
        continue;
      }

      throw new Error(message);
    } catch (error) {
      clearTimeout(timeoutId);

      const isAbort = error instanceof DOMException && error.name === "AbortError";
      const isNetwork = error instanceof TypeError;

      if (attempt < AI_REQUEST_RETRIES && (isAbort || isNetwork)) {
        const delay = Math.min(1000 * (2 ** attempt), 5000);
        await sleep(delay);
        attempt += 1;
        continue;
      }

      if (isAbort) {
        throw new Error("AI request timed out. Please try again.");
      }

      if (error instanceof Error) {
        throw error;
      }

      throw new Error("AI request failed.");
    }
  }
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
