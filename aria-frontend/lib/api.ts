// filename: lib/api.ts
// purpose: Typed HTTP client for ARIA frontend endpoints.
// dependencies: types

import type {
  CompanyProfileForm,
  GeneratePostForm,
  GeneratedPackage,
  ImportResponse,
  OnboardingStatus,
  PostResult,
  PresignResponse,
  ScheduleRequest,
  ScheduleResponse
} from "@/types";
import { IS_STATIC } from "@/lib/isStatic";
import { PREVIEW_MODE_MESSAGE, mockGeneratedContent } from "@/lib/mockData";

export interface ApiErrorPayload {
  code: string;
  message: string;
  trace_id?: string;
  retryable?: boolean;
  details?: unknown;
}

export class ApiError extends Error {
  code: string;
  trace_id?: string;
  retryable: boolean;
  details?: unknown;

  constructor(payload: ApiErrorPayload) {
    super(payload.message);
    this.name = "ApiError";
    this.code = payload.code;
    this.trace_id = payload.trace_id;
    this.retryable = Boolean(payload.retryable);
    this.details = payload.details;
  }
}

const API_BASE_RAW = process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "";
const API_BASE = API_BASE_RAW.replace(/\/$/, "");

const resolveApiBase = (): string => {
  if (API_BASE) {
    return API_BASE;
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  throw new ApiError({
    code: "API_BASE_URL_MISSING",
    message: "NEXT_PUBLIC_API_BASE_URL is not configured.",
    retryable: false,
    details: {
      required_env: "NEXT_PUBLIC_API_BASE_URL",
      alternate_env: "NEXT_PUBLIC_API_URL"
    }
  });
};

const toApiUrl = (url: string): string => `${resolveApiBase()}${url}`;

const previewPostId = "preview-post-id";

const previewGeneratedPackage: GeneratedPackage = {
  variants: [
    {
      variant_id: "preview-linkedin",
      platform: "linkedin",
      text: mockGeneratedContent.linkedin,
      char_count: mockGeneratedContent.linkedin.length,
      provider_used: "preview",
      cached: true,
      scores: {
        engagement_predicted: 74,
        tone_match: 81,
        cta_presence: 77,
        keyword_inclusion: 72,
        platform_compliance: 90,
        total: 79
      }
    },
    {
      variant_id: "preview-x",
      platform: "x",
      text: mockGeneratedContent.twitter,
      char_count: mockGeneratedContent.twitter.length,
      provider_used: "preview",
      cached: true,
      scores: {
        engagement_predicted: 69,
        tone_match: 79,
        cta_presence: 71,
        keyword_inclusion: 70,
        platform_compliance: 94,
        total: 76
      }
    }
  ],
  selected_variant_id: "preview-linkedin",
  hashtag_set: {
    broad: [
      { tag: "AriaConsole", score: 0.91 },
      { tag: "SocialMedia", score: 0.87 }
    ],
    niche: [
      { tag: "ContentPipeline", score: 0.74 },
      { tag: "CampaignOps", score: 0.7 }
    ],
    micro: [{ tag: "PreviewMode", score: 0.63 }]
  },
  audience_definition: {
    primary_demographic: {
      age_range: "25-44",
      gender_split: { female: 48, male: 47, non_binary: 5 },
      locations: ["US", "GB"]
    },
    psychographic_profile: {
      interests: ["social media", "growth"],
      values: ["clarity", "speed"],
      pain_points: ["inconsistent posting"]
    },
    platform_segments: {
      facebook_custom_audience: { include_rules: [], exclude_rules: [] },
      linkedin_audience_attributes: { job_titles: ["Marketing Manager"], industries: ["SaaS"], seniority: ["Manager"] },
      x_interest_clusters: ["marketing"],
      tiktok_interest_categories: ["business"]
    },
    natural_language_summary: "Preview audience summary for ARIA CONSOLE.",
    confidence: 0.71
  },
  posting_schedule_recommendation: [
    {
      platform: "linkedin",
      windows: [
        {
          start_local: new Date().toISOString(),
          end_local: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
          rank: 1,
          confidence: 0.78,
          reason_codes: ["industry_baseline"]
        }
      ]
    }
  ],
  seo_metadata: {
    meta_title: "ARIA Console Preview",
    meta_description: "Preview mode content metadata.",
    alt_text: "Preview image alt text",
    keywords: ["aria", "preview"]
  },
  content_quality_score: {
    overall: 78,
    subscores: {
      engagement_prediction: 76,
      tone_match: 80,
      platform_compliance: 88,
      keyword_coverage: 72,
      cta_strength: 74
    }
  }
};

const previewPostResult: PostResult = {
  post_id: previewPostId,
  status: "generated",
  generated_package_json: previewGeneratedPackage
};

const getTokenFromSession = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return sessionStorage.getItem("aria_token") ?? localStorage.getItem("aria_token");
};

const getJsonHeaders = (): HeadersInit => {
  const token = getTokenFromSession();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
};

const parseError = async (response: Response): Promise<ApiError> => {
  let payload: Partial<ApiErrorPayload> = {};
  try {
    payload = (await response.json()) as Partial<ApiErrorPayload>;
  } catch {
    payload = {};
  }
  return new ApiError({
    code: payload.code ?? `HTTP_${response.status}`,
    message: payload.message ?? `Request failed with status ${response.status}`,
    trace_id: payload.trace_id,
    retryable: payload.retryable ?? response.status >= 500,
    details: payload.details
  });
};

const requestJson = async <T>(url: string, init: RequestInit): Promise<T> => {
  if (IS_STATIC) {
    throw new ApiError({
      code: "PREVIEW_MODE_ONLY",
      message: PREVIEW_MODE_MESSAGE,
      retryable: false
    });
  }

  const response = await fetch(toApiUrl(url), {
    ...init,
    headers: {
      ...getJsonHeaders(),
      ...(init.headers ?? {})
    }
  });

  if (!response.ok) {
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
};

export const submitCompanyProfile = async (
  data: CompanyProfileForm
): Promise<{ company_id: string; profile_version: number; status: string }> => {
  if (IS_STATIC) {
    return {
      company_id: "preview-company",
      profile_version: 1,
      status: "preview"
    };
  }

  return requestJson("/v1/onboarding/company-profile", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const updateVocabulary = async (
  company_id: string,
  approved_vocabulary_list: string[],
  banned_vocabulary_list: string[]
): Promise<void> => {
  if (IS_STATIC) {
    return;
  }

  await requestJson<void>("/v1/onboarding/vocabulary", {
    method: "POST",
    body: JSON.stringify({
      company_id,
      approved_vocabulary_list,
      banned_vocabulary_list
    })
  });
};

export const importPostArchive = async (company_id: string, file: File): Promise<ImportResponse> => {
  if (IS_STATIC) {
    return {
      staged_count: 0,
      skipped_count: 0,
      import_id: "preview-import"
    };
  }

  const token = getTokenFromSession();
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(toApiUrl(`/v1/onboarding/import?company_id=${encodeURIComponent(company_id)}`), {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: form
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  return (await response.json()) as ImportResponse;
};

export const triggerQualityCheck = async (company_id: string): Promise<{ task_id: string }> => {
  if (IS_STATIC) {
    return { task_id: "preview-task-id" };
  }

  return requestJson("/v1/onboarding/quality-check", {
    method: "POST",
    body: JSON.stringify({ company_id })
  });
};

export const getOnboardingStatus = async (company_id: string): Promise<OnboardingStatus> => {
  if (IS_STATIC) {
    return {
      step: 11,
      score: 85,
      status: "preview_ready",
      remediation: []
    };
  }

  return requestJson(`/v1/onboarding/status/${company_id}`, {
    method: "GET"
  });
};

export const presignUpload = async (
  company_id: string,
  filename: string,
  content_type: string
): Promise<PresignResponse> => {
  if (IS_STATIC) {
    throw new ApiError({
      code: "PREVIEW_MODE_ONLY",
      message: PREVIEW_MODE_MESSAGE,
      retryable: false
    });
  }

  return requestJson("/v1/media/presign", {
    method: "POST",
    body: JSON.stringify({ company_id, filename, content_type })
  });
};

export const confirmUpload = async (asset_id: string): Promise<void> => {
  if (IS_STATIC) {
    return;
  }

  await requestJson<void>(`/v1/media/confirm/${asset_id}`, {
    method: "POST"
  });
};

export const uploadToPresignedUrl = async (
  url: string,
  file: File,
  onProgress: (pct: number) => void
): Promise<void> => {
  if (IS_STATIC) {
    throw new ApiError({
      code: "PREVIEW_MODE_ONLY",
      message: PREVIEW_MODE_MESSAGE,
      retryable: false
    });
  }

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url, true);
    xhr.setRequestHeader("Content-Type", file.type);
    xhr.upload.onprogress = (ev) => {
      if (ev.lengthComputable) {
        onProgress(Math.round((ev.loaded / ev.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100);
        resolve();
      } else {
        reject(new ApiError({ code: "S3_UPLOAD_FAILED", message: "Upload failed", retryable: true }));
      }
    };
    xhr.onerror = () => reject(new ApiError({ code: "S3_UPLOAD_FAILED", message: "Upload failed", retryable: true }));
    xhr.send(file);
  });
};

export const generatePost = async (
  data: GeneratePostForm
): Promise<{ post_id: string; status: "generating" | "generated"; estimated_ready_seconds: number }> => {
  if (IS_STATIC) {
    return {
      post_id: previewPostId,
      status: "generated",
      estimated_ready_seconds: 1
    };
  }

  return requestJson("/v1/posts/generate", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const getPostResult = async (post_id: string): Promise<PostResult> => {
  if (IS_STATIC) {
    return {
      ...previewPostResult,
      post_id
    };
  }

  return requestJson(`/v1/posts/${post_id}`, {
    method: "GET"
  });
};

export const getCompanyPosts = async (company_id: string, limit: number, offset: number): Promise<PostResult[]> => {
  if (IS_STATIC) {
    return [previewPostResult];
  }

  const payload = await requestJson<{ items?: PostResult[] } | PostResult[]>(
    `/v1/companies/${company_id}/posts?limit=${limit}&offset=${offset}`,
    { method: "GET" }
  );
  return Array.isArray(payload) ? payload : payload.items ?? [];
};

export const createSchedule = async (data: ScheduleRequest): Promise<ScheduleResponse> => {
  if (IS_STATIC) {
    return {
      schedule_ids: ["preview-schedule-id"],
      status: "queued"
    };
  }

  return requestJson("/v1/schedules", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const getSchedule = async (schedule_id: string): Promise<any> => {
  if (IS_STATIC) {
    return {
      id: schedule_id,
      status: "queued",
      platform: "linkedin",
      run_at_utc: new Date().toISOString()
    };
  }

  return requestJson(`/v1/schedules/${schedule_id}`, {
    method: "GET"
  });
};

export const approveSchedule = async (schedule_id: string): Promise<void> => {
  if (IS_STATIC) {
    return;
  }

  await requestJson<void>(`/v1/schedules/${schedule_id}/approve`, {
    method: "POST"
  });
};

export const getOAuthConnectUrl = (platform: string, company_id: string): string => {
  const params = new URLSearchParams({ platform, company_id });
  return toApiUrl(`/v1/oauth/connect?${params.toString()}`);
};

export const getAuditLog = async (company_id: string, limit: number, offset: number): Promise<any[]> => {
  if (IS_STATIC) {
    return [
      {
        actor: "preview-user",
        action: "preview_view",
        resource_type: "dashboard",
        created_at: new Date().toISOString()
      }
    ];
  }

  const payload = await requestJson<{ items?: any[] } | any[]>(
    `/audit/${company_id}?limit=${limit}&offset=${offset}`,
    { method: "GET" }
  );
  return Array.isArray(payload) ? payload : payload.items ?? [];
};
