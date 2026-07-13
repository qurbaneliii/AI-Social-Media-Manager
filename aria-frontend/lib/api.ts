// filename: lib/api.ts
// purpose: Typed HTTP client for ARIA frontend endpoints.
// dependencies: types

import type {
  CompanyProfileForm,
  GeneratePostForm,
  GeneratedPackage,
  OnboardingStatus,
  Platform,
  PostResult,
  ScheduleRequest,
  ScheduleResponse,
  ScheduleStatus
} from "@/types";
import { IS_STATIC } from "@/lib/isStatic";
import { PREVIEW_COMPANY_ID, PREVIEW_MODE_MESSAGE, mockGeneratedContent } from "@/lib/mockData";
import { resolvePublicApiBase } from "@/lib/api/base";
import type { components as ApiComponents } from "@/types/generated/aria-api";

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

export interface ScheduleDetail {
  id: string;
  status: ScheduleStatus;
  platform?: Platform;
  run_at_utc?: string;
  next_retry_at?: string | null;
  retry_at?: string | null;
  retry_count?: number;
  max_retries?: number;
  target?: {
    platform?: Platform;
    run_at_utc?: string;
  };
  error_code?: string | null;
  error_message?: string | null;
}

export interface AuditLogItem {
  actor?: string;
  action?: string;
  resource_type?: string;
  created_at?: string;
}

export interface SaveDraftRequest {
  company_id: string;
  platform: string;
  content: string;
  intent?: string;
  campaign_tag?: string | null;
  topic?: string | null;
  tone?: string | null;
  cta?: string | null;
}

export interface SaveDraftResponse {
  post_id: string;
  status: "draft";
  platform: string;
  created_at?: string;
}

const toApiUrl = (url: string): string => `${resolvePublicApiBase()}${url}`;

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
  return (
    sessionStorage.getItem("aria_token") ??
    sessionStorage.getItem("token") ??
    localStorage.getItem("aria_token") ??
    localStorage.getItem("token")
  );
};

const getWorkspaceId = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }
  return sessionStorage.getItem("aria_workspace_id") ?? localStorage.getItem("aria_workspace_id");
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

const getJsonHeaders = (): HeadersInit => {
  const token = getTokenFromSession();
  const workspaceId = getWorkspaceId();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(workspaceId ? { "X-ARIA-Workspace-ID": workspaceId } : {})
  };
};

const parseError = async (response: Response): Promise<ApiError> => {
  let payload: Partial<ApiErrorPayload> & { error?: Partial<ApiErrorPayload> & { request_id?: string } } = {};
  try {
    payload = (await response.json()) as Partial<ApiErrorPayload>;
  } catch {
    payload = {};
  }
  const error: Partial<ApiErrorPayload> & { request_id?: string } = payload.error ?? payload;
  return new ApiError({
    code: error.code ?? `HTTP_${response.status}`,
    message: error.message ?? `Request failed with status ${response.status}`,
    trace_id: error.trace_id ?? error.request_id,
    retryable: error.retryable ?? response.status >= 500,
    details: error.details
  });
};

const requestJson = async <T>(url: string, init: RequestInit): Promise<T> => {
  if (isPreviewMode()) {
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
  if (isPreviewMode()) {
    return {
      company_id: PREVIEW_COMPANY_ID,
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
  if (isPreviewMode()) {
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

export const triggerQualityCheck = async (company_id: string): Promise<{ task_id: string }> => {
  if (isPreviewMode()) {
    return { task_id: "preview-task-id" };
  }

  return requestJson("/v1/onboarding/quality-check", {
    method: "POST",
    body: JSON.stringify({ company_id })
  });
};

export const getOnboardingStatus = async (company_id: string): Promise<OnboardingStatus> => {
  if (isPreviewMode()) {
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

export const generatePost = async (
  data: GeneratePostForm
): Promise<{ post_id: string; status: "generating" | "generated"; estimated_ready_seconds: number }> => {
  if (isPreviewMode()) {
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
  if (isPreviewMode()) {
    return {
      ...previewPostResult,
      post_id
    };
  }

  return requestJson(`/v1/posts/${post_id}`, {
    method: "GET"
  });
};

export const saveDraftPost = async (data: SaveDraftRequest): Promise<SaveDraftResponse> => {
  if (isPreviewMode()) {
    return {
      post_id: previewPostId,
      status: "draft",
      platform: data.platform,
      created_at: new Date().toISOString()
    };
  }

  return requestJson("/v1/posts/drafts", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const getCompanyPosts = async (company_id: string, limit: number, offset: number): Promise<PostResult[]> => {
  if (isPreviewMode()) {
    return [previewPostResult];
  }

  const payload = await requestJson<{ items?: PostResult[] } | PostResult[]>(
    `/v1/companies/${company_id}/posts?limit=${limit}&offset=${offset}`,
    { method: "GET" }
  );
  return Array.isArray(payload) ? payload : payload.items ?? [];
};

export const createSchedule = async (data: ScheduleRequest): Promise<ScheduleResponse> => {
  if (isPreviewMode()) {
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

export const getSchedule = async (schedule_id: string): Promise<ScheduleDetail> => {
  if (isPreviewMode()) {
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
  if (isPreviewMode()) {
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

export const getAuditLog = async (company_id: string, limit: number, offset: number): Promise<AuditLogItem[]> => {
  if (isPreviewMode()) {
    return [
      {
        actor: "preview-user",
        action: "preview_view",
        resource_type: "dashboard",
        created_at: new Date().toISOString()
      }
    ];
  }

  void company_id;
  const payload = await requestJson<AuditLogItem[]>(`/v1/audit?limit=${limit}&offset=${offset}`, { method: "GET" });
  return payload;
};

export interface OverviewResponse {
  summary: {
    drafts: number;
    pending_approval: number;
    changes_requested: number;
    approved_internal_plans: number;
    failed_generations: number;
  };
  recent_content: Array<Record<string, unknown>>;
  upcoming_plans: Array<Record<string, unknown>>;
  source: "internal_operational_data";
  workspace_timezone: string;
}

export interface CalendarItemRecord {
  calendar_item_id: string;
  content_draft_id: string;
  platform: string;
  planned_at: string;
  timezone: string;
  planning_state: string;
  approval_status: string;
  topic?: string;
}

export interface UnscheduledContentRecord {
  draft_id: string;
  platform: string;
  topic: string;
  generation_status: string;
  approval_status: string;
  content_text?: string;
}

export type CapabilityRecord = ApiComponents["schemas"]["CapabilityStatus"];
export type CapabilitiesResponse = ApiComponents["schemas"]["CapabilitiesResponse"];

export const getOverview = (): Promise<OverviewResponse> => {
  if (isPreviewMode()) {
    return Promise.resolve({
      summary: { drafts: 0, pending_approval: 0, changes_requested: 0, approved_internal_plans: 0, failed_generations: 0 },
      recent_content: [],
      upcoming_plans: [],
      source: "internal_operational_data",
      workspace_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"
    });
  }
  return requestJson("/v1/overview", { method: "GET" });
};

export const listCalendarItems = async (filters: { platform?: string; planning_state?: string } = {}): Promise<CalendarItemRecord[]> => {
  if (isPreviewMode()) return [];
  const params = new URLSearchParams();
  if (filters.platform && filters.platform !== "all") params.set("platform", filters.platform);
  if (filters.planning_state && filters.planning_state !== "all") params.set("planning_state", filters.planning_state);
  const payload = await requestJson<{ items: CalendarItemRecord[] }>(`/v1/calendar/items?${params.toString()}`, { method: "GET" });
  return payload.items;
};

export const listUnscheduledContent = async (): Promise<UnscheduledContentRecord[]> => {
  if (isPreviewMode()) return [];
  const payload = await requestJson<{ items: UnscheduledContentRecord[] }>("/v1/calendar/unscheduled", { method: "GET" });
  return payload.items;
};

export const getCapabilities = (): Promise<CapabilitiesResponse> => {
  if (isPreviewMode()) {
    const unavailable = (detail: string): CapabilityRecord => ({ status: "Unavailable", detail, interactive: false });
    return Promise.resolve({
      database: { status: "Demo", detail: "Preview records are static and are not persisted.", interactive: false },
      authentication: { status: "Demo", detail: "Preview identity is not production authentication.", interactive: false },
      ai_provider: unavailable("No live provider is contacted in preview mode."),
      ai_mock_mode: { status: "Demo", detail: "Deterministic preview output is enabled.", interactive: false },
      media_storage: unavailable("Media storage is not implemented."),
      external_scheduling: unavailable("Calendar is internal planning only."),
      publishing: unavailable("Publishing is not implemented."),
      external_analytics: unavailable("External analytics is not implemented."),
      background_workers: unavailable("Background workers are not required for preview mode.")
    });
  }
  return requestJson("/v1/capabilities", { method: "GET" });
};
