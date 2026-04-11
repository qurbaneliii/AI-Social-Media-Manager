// filename: lib/api.ts
// purpose: Typed HTTP client for ARIA frontend endpoints.
// dependencies: types

import type {
  CompanyProfileForm,
  GeneratePostForm,
  ImportResponse,
  OnboardingStatus,
  PostResult,
  PresignResponse,
  ScheduleRequest,
  ScheduleResponse
} from "@/types";

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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

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
  const response = await fetch(`${API_BASE}${url}`, {
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
  return requestJson("/v1/onboarding/company-profile", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const updateVocabulary = async (company_id: string, approved: string[], banned: string[]): Promise<void> => {
  await requestJson<void>("/v1/onboarding/vocabulary", {
    method: "POST",
    body: JSON.stringify({ company_id, approved, banned })
  });
};

export const importPostArchive = async (company_id: string, file: File): Promise<ImportResponse> => {
  const token = getTokenFromSession();
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/v1/onboarding/import?company_id=${encodeURIComponent(company_id)}`, {
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
  return requestJson("/v1/onboarding/quality-check", {
    method: "POST",
    body: JSON.stringify({ company_id })
  });
};

export const getOnboardingStatus = async (company_id: string): Promise<OnboardingStatus> => {
  return requestJson(`/v1/onboarding/status/${company_id}`, {
    method: "GET"
  });
};

export const presignUpload = async (
  company_id: string,
  filename: string,
  content_type: string
): Promise<PresignResponse> => {
  return requestJson("/v1/media/presign", {
    method: "POST",
    body: JSON.stringify({ company_id, filename, content_type })
  });
};

export const confirmUpload = async (asset_id: string): Promise<void> => {
  await requestJson<void>(`/v1/media/confirm/${asset_id}`, {
    method: "POST"
  });
};

export const uploadToPresignedUrl = async (
  url: string,
  file: File,
  onProgress: (pct: number) => void
): Promise<void> => {
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
  return requestJson("/v1/posts/generate", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const getPostResult = async (post_id: string): Promise<PostResult> => {
  return requestJson(`/v1/posts/${post_id}`, {
    method: "GET"
  });
};

export const getCompanyPosts = async (company_id: string, limit: number, offset: number): Promise<PostResult[]> => {
  const payload = await requestJson<{ items?: PostResult[] } | PostResult[]>(
    `/v1/companies/${company_id}/posts?limit=${limit}&offset=${offset}`,
    { method: "GET" }
  );
  return Array.isArray(payload) ? payload : payload.items ?? [];
};

export const createSchedule = async (data: ScheduleRequest): Promise<ScheduleResponse> => {
  return requestJson("/v1/schedules", {
    method: "POST",
    body: JSON.stringify(data)
  });
};

export const getSchedule = async (schedule_id: string): Promise<any> => {
  return requestJson(`/v1/schedules/${schedule_id}`, {
    method: "GET"
  });
};

export const approveSchedule = async (schedule_id: string): Promise<void> => {
  await requestJson<void>(`/v1/schedules/${schedule_id}/approve`, {
    method: "POST"
  });
};

export const getOAuthConnectUrl = (platform: string, company_id: string): string => {
  const params = new URLSearchParams({ platform, company_id });
  return `${API_BASE}/v1/oauth/connect?${params.toString()}`;
};

export const getAuditLog = async (company_id: string, limit: number, offset: number): Promise<any[]> => {
  const payload = await requestJson<{ items?: any[] } | any[]>(
    `/audit/${company_id}?limit=${limit}&offset=${offset}`,
    { method: "GET" }
  );
  return Array.isArray(payload) ? payload : payload.items ?? [];
};
