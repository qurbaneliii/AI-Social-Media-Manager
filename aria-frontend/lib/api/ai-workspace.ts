export interface ProductContext {
  product_name: string;
  product_role: string;
  default_workflow_mode: string;
  supported_capabilities: string[];
  automation_boundaries: string[];
  default_safety_rules: string[];
  required_brand_inputs: string[];
  optional_manual_data_inputs: string[];
}

export interface BrandProfile {
  brand_id: string;
  brand_name: string;
  industry: string;
  description: string;
  products_or_services: string[];
  target_audience: string[];
  tone_of_voice: string[];
  brand_values: string[];
  forbidden_topics: string[];
  forbidden_words: string[];
  approved_claims: string[];
  competitors: string[];
  platforms: string[];
  visual_style: Record<string, unknown>;
  business_goals: string[];
  language_preferences: string[];
}

export interface BrandProfileValidationResult {
  brand_id: string;
  completeness_score: number;
  is_complete: boolean;
  required_fields: string[];
  missing_required_fields: string[];
  warnings: string[];
  using_default_context: boolean;
}

export interface BrandProfileResponse {
  profile: BrandProfile;
  validation: BrandProfileValidationResult;
  product_context: ProductContext;
  persisted: boolean;
}

export interface PlatformContext {
  platform: string;
  content_type: string;
  audience_segment?: string;
  objective: string;
  tone_override?: string | null;
  character_limit?: number | null;
  hashtag_limit?: number | null;
  format_rules?: string[];
}

export interface ContentRequest {
  brand_profile: BrandProfile;
  platform_context: PlatformContext;
  campaign_objective: string;
  topic: string;
  content_pillar: string;
  language?: string;
  number_of_variants?: number;
  extra_context?: Record<string, unknown>;
}

export interface GeneratedContentPackage {
  platform: string;
  content_type: string;
  hook: string;
  caption: string;
  cta: string;
  hashtags: string[];
  visual_brief: Record<string, unknown>;
  video_script?: string | null;
  carousel_structure: Record<string, unknown>[];
  posting_recommendation: Record<string, unknown>;
  rationale: string;
  risks: string[];
  quality_scores?: AIQualityReview | null;
}

export interface AIQualityReview {
  brand_consistency_score: number;
  platform_fit_score: number;
  clarity_score: number;
  cta_strength_score: number;
  originality_score: number;
  factual_risk_score: number;
  safety_risk_score: number;
  engagement_potential_score: number;
  approval_status: "approved" | "needs_revision" | "requires_human_review";
  improvement_notes: string[];
}

export interface ContentRefinementResponse {
  improved: string;
  mock_mode: boolean;
  route: string;
}

export interface BrandStrategyRequest {
  brand_profile: BrandProfile;
  business_goal: string;
  platforms: string[];
  market_context?: Record<string, unknown>;
}

export interface BrandStrategyPlan {
  positioning_statement: string;
  audience_hypotheses: string[];
  content_pillars: string[];
  campaign_angles: string[];
  platform_recommendations: Record<string, string[]>;
  strategic_recommendations: string[];
  risks: string[];
  approval_required: boolean;
}

export interface CompetitorPostData {
  competitor_name: string;
  platform: string;
  content_type: string;
  caption: string;
  hook?: string | null;
  hashtags?: string[];
  published_at?: string | null;
  engagement_metrics?: Record<string, number>;
  metadata?: Record<string, unknown>;
}

export interface CompetitorAnalysisRequest {
  brand_profile: BrandProfile;
  competitors: CompetitorPostData[];
  business_goal?: string;
  platforms?: string[];
}

export interface CompetitorInsightReport {
  top_performing_content_types: string[];
  hook_patterns: string[];
  recurring_themes: string[];
  hashtag_patterns: string[];
  tone_patterns: string[];
  posting_patterns: string[];
  content_gaps: string[];
  strategic_opportunities: string[];
  risk_notes: string[];
  source_limitations: string[];
}

export interface TrendInputData {
  keyword: string;
  source?: string;
  platform?: string | null;
  signals?: Record<string, unknown>;
  examples?: string[];
}

export interface TrendResearchRequest {
  brand_profile: BrandProfile;
  trends: TrendInputData[];
  platforms?: string[];
  business_goal?: string;
}

export interface TrendInsightReport {
  relevant_topics: string[];
  recommended_hashtags: string[];
  content_formats: string[];
  trend_opportunities: string[];
  platform_notes: Record<string, string[]>;
  risk_notes: string[];
  source_limitations: string[];
}

export interface HashtagRecommendationRequest {
  brand_profile: BrandProfile;
  platform_context: PlatformContext;
  topic: string;
  campaign_name?: string | null;
  location?: string | null;
  trend_keywords?: string[];
  max_hashtags?: number;
}

export interface HashtagRecommendation {
  niche_hashtags: string[];
  broad_hashtags: string[];
  branded_hashtags: string[];
  campaign_hashtags: string[];
  location_hashtags: string[];
  trend_based_hashtags: string[];
  risk_notes: string[];
  rationale: string;
}

export interface VisualConceptRequest {
  brand_profile: BrandProfile;
  platform_context: PlatformContext;
  topic: string;
  content_pillar: string;
  campaign_objective: string;
  creative_constraints?: string[];
}

export interface VisualConceptPackage {
  visual_brief: string;
  carousel_concepts: Record<string, unknown>[];
  short_form_video_concepts: Record<string, unknown>[];
  image_generation_prompts: string[];
  design_direction: Record<string, unknown>;
  mood: string[];
  scene: string;
  layout: string;
  creative_constraints: string[];
  risk_notes: string[];
}

export interface CalendarPlanningRequest {
  brand_profile: BrandProfile;
  start_date: string;
  end_date: string;
  platforms: string[];
  content_pillars: string[];
  campaign_objectives: string[];
  posting_frequency_per_week: number;
  preferred_content_types: string[];
  timezone?: string;
}

export interface ContentCalendarItem {
  date: string;
  time: string;
  platform: string;
  content_pillar: string;
  objective: string;
  topic: string;
  content_type: string;
  draft_status: string;
  rationale: string;
  approval_required: boolean;
}

export interface ContentCalendarPlan {
  items: ContentCalendarItem[];
  rationale: string;
  risk_notes: string[];
  approval_required: boolean;
}

export interface CommunityManagementRequest {
  brand_profile: BrandProfile;
  platform: string;
  message_text: string;
  author_context?: Record<string, string>;
  conversation_context?: string[];
}

export interface CommunityMessageAnalysis {
  message_text: string;
  sentiment: string;
  intent: string;
  urgency: string;
  toxicity_risk: number;
  crisis_risk: number;
  complaint_type?: string | null;
  buying_intent: boolean;
  faq_intent: boolean;
  suggested_reply: string;
  confidence: number;
  requires_human_review: boolean;
  escalation_reason?: string | null;
  auto_reply_allowed: boolean;
}

export interface ReportingInsightRequest {
  brand_profile: BrandProfile;
  reporting_period: string;
  platforms: string[];
  analytics_data: Record<string, unknown>;
  campaign_goals: string[];
}

export interface ReportingInsightReport {
  summary: string;
  what_worked: string[];
  what_failed: string[];
  recommended_changes: string[];
  next_experiments: string[];
  risk_notes: string[];
  chart_ready_data: Record<string, unknown>;
}

export class AIWorkspaceApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "AIWorkspaceApiError";
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE_ENV_KEYS = [
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_AI_ORCHESTRATION_URL",
  "NEXT_PUBLIC_API_URL"
] as const;

export const defaultBrandProfile: BrandProfile = {
  brand_id: "brand-1",
  brand_name: "ARIA Labs",
  industry: "Marketing software",
  description: "Approval-based AI social media management workspace.",
  products_or_services: ["AI content workspace", "approval workflow"],
  target_audience: ["founders", "marketing teams"],
  tone_of_voice: ["clear", "strategic", "useful"],
  brand_values: ["human control", "responsible automation"],
  forbidden_topics: ["medical advice", "legal advice"],
  forbidden_words: ["guaranteed", "viral overnight"],
  approved_claims: ["Helps teams review AI-generated social media drafts."],
  competitors: [],
  platforms: ["linkedin"],
  visual_style: { palette: ["teal", "slate"], style: "clean dashboard visuals" },
  business_goals: ["increase content quality"],
  language_preferences: ["en"]
};

function resolveApiBase(): string {
  for (const key of API_BASE_ENV_KEYS) {
    const value = process.env[key];
    if (value) {
      return value.replace(/\/$/, "");
    }
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  throw new AIWorkspaceApiError(
    "NEXT_PUBLIC_API_BASE_URL is not configured.",
    0,
    {
      required_env: "NEXT_PUBLIC_API_BASE_URL",
      compatibility_fallback_env: ["NEXT_PUBLIC_AI_ORCHESTRATION_URL", "NEXT_PUBLIC_API_URL"]
    }
  );
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

async function parseError(response: Response): Promise<AIWorkspaceApiError> {
  let detail: unknown;
  try {
    detail = await response.json();
  } catch {
    detail = await response.text();
  }

  let message = response.statusText || "AI workspace request failed";
  if (detail && typeof detail === "object" && "detail" in detail) {
    const parsedDetail = (detail as { detail?: unknown }).detail;
    message = typeof parsedDetail === "string" ? parsedDetail : JSON.stringify(parsedDetail);
  } else if (typeof detail === "string" && detail.trim()) {
    message = detail;
  }

  return new AIWorkspaceApiError(message, response.status, detail);
}

async function requestAI<TResponse>(path: string, init: RequestInit = {}): Promise<TResponse> {
  const token = getAuthToken();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${resolveApiBase()}${path}`, { ...init, headers });
  if (!response.ok) {
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as TResponse;
  }
  return (await response.json()) as TResponse;
}

function postJson<TResponse>(path: string, payload: unknown): Promise<TResponse> {
  return requestAI<TResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getWorkspaceContext(): Promise<ProductContext> {
  return requestAI("/internal/ai/workspace-context");
}

export function getBrandProfile(brandId: string): Promise<BrandProfileResponse> {
  return requestAI(`/internal/ai/brand-profile/${encodeURIComponent(brandId)}`);
}

export function upsertBrandProfile(profile: BrandProfile): Promise<BrandProfileResponse> {
  return postJson("/internal/ai/brand-profile", { profile });
}

export function validateBrandProfile(
  profile: BrandProfile,
  usingDefaultContext = false
): Promise<BrandProfileValidationResult> {
  return postJson("/internal/ai/brand-profile/validate", {
    profile,
    using_default_context: usingDefaultContext
  });
}

export function generateContentPackage(payload: ContentRequest): Promise<GeneratedContentPackage> {
  return postJson("/internal/ai/generate-content-package", payload);
}

export function refineContent(payload: { content: string; instruction: string }): Promise<ContentRefinementResponse> {
  return postJson("/internal/ai/content/refine", payload);
}

export function createBrandStrategy(payload: BrandStrategyRequest): Promise<BrandStrategyPlan> {
  return postJson("/internal/ai/brand-strategy", payload);
}

export function analyzeCompetitors(payload: CompetitorAnalysisRequest): Promise<CompetitorInsightReport> {
  return postJson("/internal/ai/competitors/analyze", payload);
}

export function researchTrends(payload: TrendResearchRequest): Promise<TrendInsightReport> {
  return postJson("/internal/ai/trends/research", payload);
}

export function recommendHashtags(payload: HashtagRecommendationRequest): Promise<HashtagRecommendation> {
  return postJson("/internal/ai/hashtags/recommend", payload);
}

export function generateVisualConcept(payload: VisualConceptRequest): Promise<VisualConceptPackage> {
  return postJson("/internal/ai/visual-concept", payload);
}

export function createContentCalendar(payload: CalendarPlanningRequest): Promise<ContentCalendarPlan> {
  return postJson("/internal/ai/content-calendar", payload);
}

export function analyzeCommunityMessage(payload: CommunityManagementRequest): Promise<CommunityMessageAnalysis> {
  return postJson("/internal/ai/community/analyze", payload);
}

export function generateReportInsights(payload: ReportingInsightRequest): Promise<ReportingInsightReport> {
  return postJson("/internal/ai/reports/insights", payload);
}

export function reviewContentQuality(payload: {
  request: ContentRequest;
  package: GeneratedContentPackage;
}): Promise<AIQualityReview> {
  return postJson("/internal/ai/content-quality/review", payload);
}
