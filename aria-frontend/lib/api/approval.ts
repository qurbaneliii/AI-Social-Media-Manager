export type ApprovalObjectType = "content_draft" | "calendar_draft" | "community_reply" | "report_draft";

export type ApprovalStatus =
  | "draft"
  | "in_review"
  | "approved"
  | "rejected"
  | "changes_requested"
  | "ready_for_scheduling"
  | "escalated"
  | "archived";

export type ApprovalAction =
  | "submit"
  | "approve"
  | "reject"
  | "request_changes"
  | "archive"
  | "mark_ready_for_scheduling"
  | "escalate"
  | "reset_to_draft";

export interface ApprovalQueueFilters {
  brand_id?: string;
  status?: ApprovalStatus | "";
  object_type?: ApprovalObjectType | "";
  platform?: string;
  limit?: number;
  offset?: number;
  created_after?: string;
  created_before?: string;
}

export interface ApprovalQueueItemBase {
  object_id: string;
  object_type: ApprovalObjectType;
  brand_id: string;
  approval_status: ApprovalStatus;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ContentDraftQueueItem extends ApprovalQueueItemBase {
  object_type: "content_draft";
  draft_id: string;
  platform: string;
  content_type: string;
  topic: string;
  hook_preview: string;
  caption_preview: string;
  requires_human_review: boolean;
  risk_summary: string[];
  quality_score_summary: Record<string, string | number | boolean | null>;
  model?: string | null;
  mock_mode?: boolean | null;
}

export interface CalendarDraftQueueItem extends ApprovalQueueItemBase {
  object_type: "calendar_draft";
  item_id: string;
  platform: string;
  planned_date?: string | null;
  planned_time?: string | null;
  content_pillar: string;
  objective: string;
  topic: string;
  readiness_status?: string | null;
}

export interface CommunityReplyQueueItem extends ApprovalQueueItemBase {
  object_type: "community_reply";
  reply_draft_id: string;
  original_message_preview: string;
  suggested_reply_preview: string;
  sentiment: string;
  intent: string;
  urgency: string;
  toxicity_risk: number;
  crisis_risk: number;
  requires_human_review: boolean;
  escalation_reason?: string | null;
  auto_reply_allowed: boolean;
}

export interface ReportDraftQueueItem extends ApprovalQueueItemBase {
  object_type: "report_draft";
  report_id: string;
  report_type: string;
  date_range: string;
  summary_preview: string;
}

export type ApprovalQueueItem =
  | ContentDraftQueueItem
  | CalendarDraftQueueItem
  | CommunityReplyQueueItem
  | ReportDraftQueueItem;

export interface ApprovalQueueResponse<TItem extends ApprovalQueueItem = ApprovalQueueItem> {
  items: TItem[];
  count: number;
  limit: number;
  offset: number;
}

export interface ApprovalActionRequest {
  object_id: string;
  object_type: ApprovalObjectType;
  reviewer_id?: string;
  reviewer_role?: string;
  reason?: string;
  requested_changes?: string[];
  metadata?: Record<string, unknown>;
}

export interface ApprovalDecisionRequest extends ApprovalActionRequest {
  previous_status?: ApprovalStatus | null;
  new_status: ApprovalStatus;
  action: ApprovalAction;
  timestamp?: string;
}

export interface ApprovalDecision {
  object_id: string;
  object_type: ApprovalObjectType;
  previous_status?: ApprovalStatus | null;
  new_status: ApprovalStatus;
  action: ApprovalAction;
  reviewer_id?: string | null;
  reviewer_role?: string | null;
  reason: string;
  requested_changes: string[];
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface ApprovalAuditEvent extends ApprovalDecision {
  event_id?: string | null;
}

export interface ApprovalAuditTimeline {
  object_id: string;
  object_type: ApprovalObjectType;
  events: ApprovalAuditEvent[];
  latest_requested_changes: string[];
  last_review_reason: string;
}

export interface ApprovalResult {
  decision: ApprovalDecision;
  audit_event: ApprovalAuditEvent;
  record: Record<string, unknown>;
}

export type ReviewValue = string | number | boolean | null;

export interface ApprovalDetailBase {
  object_type: ApprovalObjectType;
  brand_id: string;
  approval_status: ApprovalStatus;
  created_at?: string | null;
  updated_at?: string | null;
  latest_audit_events: ApprovalAuditEvent[];
  last_requested_changes: string[];
  last_review_reason: string;
}

export interface ContentDraftDetail extends ApprovalDetailBase {
  object_type: "content_draft";
  draft_id: string;
  platform: string;
  content_type: string;
  topic: string;
  hook: string;
  caption: string;
  cta: string;
  hashtags: string[];
  visual_brief_summary: string;
  video_script_summary: string;
  carousel_structure_summary: string[];
  posting_recommendation: Record<string, ReviewValue>;
  rationale: string;
  risk_summary: string[];
  quality_score_summary: Record<string, ReviewValue>;
  requires_human_review: boolean;
  model?: string | null;
  mock_mode?: boolean | null;
  prompt_version?: string | null;
}

export interface CalendarDraftDetail extends ApprovalDetailBase {
  object_type: "calendar_draft";
  item_id: string;
  platform: string;
  planned_date?: string | null;
  planned_time?: string | null;
  content_pillar: string;
  objective: string;
  topic: string;
  content_type: string;
  rationale: string;
  readiness_status?: string | null;
}

export interface CommunityReplyDraftDetail extends ApprovalDetailBase {
  object_type: "community_reply";
  reply_draft_id: string;
  original_message_text: string;
  suggested_reply: string;
  sentiment: string;
  intent: string;
  urgency: string;
  toxicity_risk: number;
  crisis_risk: number;
  confidence: number;
  requires_human_review: boolean;
  escalation_reason?: string | null;
  auto_reply_allowed: boolean;
}

export interface ReportDraftDetail extends ApprovalDetailBase {
  object_type: "report_draft";
  report_id: string;
  report_type: string;
  date_range: string;
  summary: string;
  key_insights: string[];
  recommendations: string[];
}

export type ApprovalDetail =
  | ContentDraftDetail
  | CalendarDraftDetail
  | CommunityReplyDraftDetail
  | ReportDraftDetail;

export interface RequestChangesPayload extends ApprovalActionRequest {
  reason: string;
  requested_changes: string[];
}

export class ApprovalApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApprovalApiError";
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE_ENV_KEYS = [
  "NEXT_PUBLIC_AI_ORCHESTRATION_URL",
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_API_URL"
] as const;

function resolveApprovalApiBase(): string {
  for (const key of API_BASE_ENV_KEYS) {
    const value = process.env[key];
    if (value) {
      return value.replace(/\/$/, "");
    }
  }
  return "http://localhost:8000";
}

function buildQuery(filters: ApprovalQueueFilters = {}): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return (
    window.localStorage.getItem("auth_token") ??
    window.localStorage.getItem("token") ??
    window.sessionStorage.getItem("auth_token") ??
    window.sessionStorage.getItem("token")
  );
}

async function parseError(response: Response): Promise<ApprovalApiError> {
  let detail: unknown;
  try {
    detail = await response.json();
  } catch {
    detail = await response.text();
  }

  let message = response.statusText || "Approval API request failed";
  if (detail && typeof detail === "object" && "detail" in detail) {
    const parsedDetail = (detail as { detail?: unknown }).detail;
    message = typeof parsedDetail === "string" ? parsedDetail : JSON.stringify(parsedDetail);
  } else if (typeof detail === "string" && detail.trim()) {
    message = detail;
  }

  return new ApprovalApiError(message, response.status, detail);
}

async function requestApprovalApi<TResponse>(path: string, init: RequestInit = {}): Promise<TResponse> {
  const token = getAuthToken();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${resolveApprovalApiBase()}${path}`, {
    ...init,
    headers
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

function actionBody(payload: ApprovalActionRequest | ApprovalDecisionRequest): string {
  return JSON.stringify(payload);
}

export function listApprovalQueue(filters?: ApprovalQueueFilters): Promise<ApprovalQueueResponse> {
  return requestApprovalApi(`/internal/ai/approval/queue${buildQuery(filters)}`);
}

export function listContentApprovalQueue(
  filters?: Omit<ApprovalQueueFilters, "object_type">
): Promise<ApprovalQueueResponse<ContentDraftQueueItem>> {
  return requestApprovalApi(`/internal/ai/approval/queue/content${buildQuery(filters)}`);
}

export function listCalendarApprovalQueue(
  filters?: Omit<ApprovalQueueFilters, "object_type">
): Promise<ApprovalQueueResponse<CalendarDraftQueueItem>> {
  return requestApprovalApi(`/internal/ai/approval/queue/calendar${buildQuery(filters)}`);
}

export function listCommunityApprovalQueue(
  filters?: Omit<ApprovalQueueFilters, "object_type">
): Promise<ApprovalQueueResponse<CommunityReplyQueueItem>> {
  return requestApprovalApi(`/internal/ai/approval/queue/community${buildQuery(filters)}`);
}

export function listReportApprovalQueue(
  filters?: Omit<ApprovalQueueFilters, "object_type">
): Promise<ApprovalQueueResponse<ReportDraftQueueItem>> {
  return requestApprovalApi(`/internal/ai/approval/queue/reports${buildQuery(filters)}`);
}

export function getApprovalDetail(objectType: ApprovalObjectType, objectId: string): Promise<ApprovalDetail> {
  return requestApprovalApi(
    `/internal/ai/approval/detail/${encodeURIComponent(objectType)}/${encodeURIComponent(objectId)}`
  );
}

export function getContentDraftDetail(draftId: string): Promise<ContentDraftDetail> {
  return requestApprovalApi(`/internal/ai/approval/detail/content/${encodeURIComponent(draftId)}`);
}

export function getCalendarDraftDetail(itemId: string): Promise<CalendarDraftDetail> {
  return requestApprovalApi(`/internal/ai/approval/detail/calendar/${encodeURIComponent(itemId)}`);
}

export function getCommunityReplyDetail(replyDraftId: string): Promise<CommunityReplyDraftDetail> {
  return requestApprovalApi(`/internal/ai/approval/detail/community/${encodeURIComponent(replyDraftId)}`);
}

export function getReportDraftDetail(reportId: string): Promise<ReportDraftDetail> {
  return requestApprovalApi(`/internal/ai/approval/detail/reports/${encodeURIComponent(reportId)}`);
}

export function applyApprovalDecision(payload: ApprovalDecisionRequest): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/decision", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function submitForReview(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/submit", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function approveDraft(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/approve", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function rejectDraft(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/reject", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function requestDraftChanges(payload: RequestChangesPayload): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/request-changes", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function archiveDraft(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return requestApprovalApi("/internal/ai/approval/archive", {
    method: "POST",
    body: actionBody(payload)
  });
}

export function markCalendarReadyForScheduling(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return applyApprovalDecision({
    ...payload,
    object_type: "calendar_draft",
    action: "mark_ready_for_scheduling",
    new_status: "ready_for_scheduling"
  });
}

export function escalateCommunityReply(payload: ApprovalActionRequest): Promise<ApprovalResult> {
  return applyApprovalDecision({
    ...payload,
    object_type: "community_reply",
    action: "escalate",
    new_status: "escalated"
  });
}

export function listApprovalAuditEvents(
  objectType: ApprovalObjectType,
  objectId: string
): Promise<ApprovalAuditEvent[]> {
  return requestApprovalApi(
    `/internal/ai/approval/audit/${encodeURIComponent(objectType)}/${encodeURIComponent(objectId)}`
  );
}
