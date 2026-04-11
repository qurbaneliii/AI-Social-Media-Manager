// filename: types/index.ts
// purpose: Shared frontend contracts mapped directly to ARIA backend responses and requests.
// dependencies: none

export type Platform = "instagram" | "linkedin" | "facebook" | "x" | "tiktok" | "pinterest";

export type PostIntent =
  | "announce"
  | "educate"
  | "promote"
  | "engage"
  | "inspire"
  | "crisis_response";

export type CTAType = "learn_more" | "book_demo" | "buy_now" | "download" | "comment" | "share";

export type ScheduleStatus =
  | "queued"
  | "awaiting_approval"
  | "publishing"
  | "published"
  | "failed"
  | "dead_letter";

export type UserRole = "agency_admin" | "brand_manager" | "content_creator" | "analyst";

export interface CompanyProfileForm {
  company_name: string;
  industry_vertical: string;
  target_market: {
    regions: string[];
    segments: Array<"B2B" | "B2C" | "D2C">;
    persona_summary: string;
  };
  brand_positioning_statement: string;
  tone_of_voice_descriptors: string[];
  competitor_list: string[];
  platform_presence: Record<Platform, boolean>;
  posting_frequency_goal: Record<Platform, number>;
  primary_cta_types: CTAType[];
  brand_color_hex_codes: string[];
  approved_vocabulary_list: string[];
  banned_vocabulary_list: string[];
  logo_file: string | null;
  sample_post_images: string[];
}

export interface OnboardingStatus {
  step: number;
  score: number | null;
  status: string;
  remediation: string[] | null;
}

export interface GeneratePostForm {
  company_id: string;
  post_intent: PostIntent;
  core_message: string;
  target_platforms: Platform[];
  campaign_tag?: string;
  attached_media_id?: string;
  manual_keywords?: string[];
  urgency_level: "scheduled" | "immediate";
  requested_publish_at?: string;
}

export interface PostVariant {
  variant_id: string;
  platform: Platform;
  text: string;
  char_count: number;
  provider_used?: string;
  cached?: boolean;
  scores: {
    engagement_predicted: number;
    tone_match: number;
    cta_presence: number;
    keyword_inclusion: number;
    platform_compliance: number;
    total: number;
  };
}

export interface HashtagItem {
  tag: string;
  score: number;
}

export interface HashtagSet {
  broad: HashtagItem[];
  niche: HashtagItem[];
  micro: HashtagItem[];
}

export interface PrimaryDemographic {
  age_range: string;
  gender_split: { female: number; male: number; non_binary: number };
  locations: string[];
}

export interface PsychographicProfile {
  interests: string[];
  values: string[];
  pain_points: string[];
}

export interface PlatformSegments {
  facebook_custom_audience: { include_rules: any[]; exclude_rules: any[] };
  linkedin_audience_attributes: { job_titles: string[]; industries: string[]; seniority: string[] };
  x_interest_clusters: string[];
  tiktok_interest_categories: string[];
}

export interface AudienceDefinition {
  primary_demographic: PrimaryDemographic;
  psychographic_profile: PsychographicProfile;
  platform_segments: PlatformSegments;
  natural_language_summary: string;
  confidence: number;
}

export type ReasonCode = "historical_win" | "industry_baseline" | "low_competitor_density";

export interface PostingWindow {
  start_local: string;
  end_local: string;
  rank: number;
  confidence: number;
  reason_codes: ReasonCode[];
}

export interface PostingScheduleRecommendation {
  platform: Platform;
  windows: PostingWindow[];
}

export interface SeoMetadata {
  meta_title: string;
  meta_description: string;
  alt_text: string;
  keywords: string[];
}

export interface ContentQualityScore {
  overall: number;
  subscores: {
    engagement_prediction: number;
    tone_match: number;
    platform_compliance: number;
    keyword_coverage: number;
    cta_strength: number;
  };
}

export interface GeneratedPackage {
  variants: PostVariant[];
  selected_variant_id: string;
  hashtag_set: HashtagSet;
  audience_definition: AudienceDefinition;
  posting_schedule_recommendation: PostingScheduleRecommendation[];
  seo_metadata: SeoMetadata;
  content_quality_score: ContentQualityScore;
}

export interface PostResult {
  post_id: string;
  status: "generating" | "generated" | "failed";
  generated_package_json: GeneratedPackage;
}

export interface ScheduleTarget {
  platform: Platform;
  run_at_utc: string;
}

export interface ScheduleRequest {
  post_id: string;
  company_id: string;
  targets: ScheduleTarget[];
  approval_mode: "human" | "auto";
  manual_override?: { timezone: string; force_window: boolean };
}

export interface ScheduleResponse {
  schedule_ids: string[];
  status: "queued";
}

export interface PresignResponse {
  upload_url: string;
  asset_id: string;
}

export interface ImportResponse {
  staged_count: number;
  skipped_count: number;
  import_id?: string;
}

export interface QualityCheckResponse {
  task_id: string;
}

export interface PlatformCredentialStatus {
  status: "disconnected" | "connected" | "expired";
  account_ref?: string;
  token_expires_at?: string;
  updated_at?: string;
}

export interface ToneFingerprint {
  formality_score: number;
  humor_score: number;
  assertiveness_score: number;
  optimism_score: number;
}

export interface LLMProxyResponse {
  provider_used: string;
  cached: boolean;
  trace_id?: string;
}

export interface AgencyWorkspace {
  workspace_id: string;
  workspace_name: string;
  company_id: string;
}

export interface WorkspaceMember {
  user_id: string;
  email: string;
  role: UserRole;
  workspace_id: string;
}
