import { z } from "zod";

export const UuidSchema = z.string().uuid();
export const IsoDatetimeSchema = z.string().datetime({ offset: true });
export const PlatformSchema = z.enum(["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"]);

export const CompanyOnboardingRequestSchema = z.object({
  company_name: z.string().min(2).max(120),
  industry_vertical: z.string(),
  target_market: z.object({
    regions: z.array(z.string().length(2)),
    segments: z.array(z.enum(["B2B", "B2C", "D2C"])),
    persona_summary: z.string()
  }),
  brand_positioning_statement: z.string().min(30).max(500),
  tone_of_voice_descriptors: z.array(z.string()),
  competitor_list: z.array(z.string()),
  platform_presence: z.object({
    instagram: z.boolean(),
    linkedin: z.boolean(),
    facebook: z.boolean(),
    x: z.boolean(),
    tiktok: z.boolean(),
    pinterest: z.boolean()
  }),
  posting_frequency_goal: z.object({
    instagram: z.number().int(),
    linkedin: z.number().int(),
    facebook: z.number().int(),
    x: z.number().int(),
    tiktok: z.number().int(),
    pinterest: z.number().int()
  }),
  primary_cta_types: z.array(z.string()),
  brand_color_hex_codes: z.array(z.string().regex(/^#[0-9A-Fa-f]{6}$/)),
  approved_vocabulary_list: z.array(z.string()),
  banned_vocabulary_list: z.array(z.string()),
  previous_post_archive: z.object({
    format: z.enum(["csv", "json"]),
    s3_uri: z.string().optional()
  }).optional(),
  brand_guidelines_pdf: z.string().optional(),
  logo_file: UuidSchema.optional(),
  sample_post_images: z.array(UuidSchema.optional())
});

export const CompanyOnboardingResponseSchema = z.object({
  company_id: UuidSchema,
  profile_version: z.number().int(),
  status: z.literal("submitted")
});

export const MediaPresignRequestSchema = z.object({
  company_id: UuidSchema,
  file_name: z.string().min(1),
  mime_type: z.string().min(1),
  size_bytes: z.number().int().positive()
});

export const MediaPresignResponseSchema = z.object({
  media_id: UuidSchema,
  upload_url: z.string().url(),
  s3_key: z.string()
});

export const PostGenerateRequestSchema = z.object({
  company_id: UuidSchema,
  post_intent: z.enum(["announce", "educate", "promote", "engage", "inspire", "crisis_response"]),
  core_message: z.string().min(20).max(500),
  target_platforms: z.array(PlatformSchema),
  campaign_tag: z.string().optional(),
  attached_media_id: UuidSchema.optional(),
  manual_keywords: z.array(z.string()),
  urgency_level: z.enum(["scheduled", "immediate"]),
  requested_publish_at: IsoDatetimeSchema.optional()
});

export const PostGenerateResponseSchema = z.object({
  post_id: UuidSchema,
  status: z.enum(["generating", "generated"]),
  estimated_ready_seconds: z.number().int()
});

export const ScheduleCreateRequestSchema = z.object({
  post_id: UuidSchema,
  company_id: UuidSchema,
  targets: z.array(z.object({
    platform: PlatformSchema,
    run_at_utc: IsoDatetimeSchema
  })).min(1),
  approval_mode: z.enum(["human", "auto"]),
  manual_override: z.object({
    timezone: z.string(),
    force_window: z.boolean()
  })
});

export const ScheduleCreateResponseSchema = z.object({
  schedule_ids: z.array(UuidSchema),
  status: z.literal("queued")
});

export const ScheduleApproveResponseSchema = z.object({
  schedule_id: UuidSchema,
  status: z.enum(["approved", "awaiting_approval", "published", "failed"]) 
});

export const PublishNowRequestSchema = z.object({
  post_id: UuidSchema,
  company_id: UuidSchema,
  platform: PlatformSchema
});

export const CanonicalPublishPayloadSchema = z.object({
  schedule_id: UuidSchema,
  company_id: UuidSchema,
  platform: PlatformSchema,
  content: z.object({
    caption_text: z.string(),
    hashtags: z.array(z.string()),
    media: z.array(z.object({
      s3_key: z.string(),
      mime_type: z.string()
    })),
    alt_text: z.string().optional()
  }),
  credentials_ref: UuidSchema.optional(),
  idempotency_key: z.string().optional(),
  tracking: z.object({
    campaign_tag: z.string(),
    utm: z.object({
      source: z.string(),
      medium: z.string(),
      campaign: z.string()
    })
  }).optional()
});

export const PublishResponseSchema = z.object({
  status: z.enum(["published", "failed"]),
  external_post_id: z.string().optional(),
  error: z.object({
    code: z.string(),
    message: z.string()
  }).optional()
});

export const AnalyticsIngestRequestSchema = z.object({
  records: z.array(z.object({
    post_id: UuidSchema,
    platform: z.string(),
    external_post_id: z.string(),
    impressions: z.number().int(),
    reach: z.number().int(),
    engagement_rate: z.number(),
    click_through_rate: z.number(),
    saves: z.number().int(),
    shares: z.number().int(),
    follower_growth_delta: z.number().int(),
    posting_timestamp: IsoDatetimeSchema,
    captured_at: IsoDatetimeSchema
  }))
});

export const AnalyticsIngestResponseSchema = z.object({
  ingested_count: z.number().int(),
  rejected_count: z.number().int(),
  errors: z.array(z.object({
    index: z.number().int(),
    reason: z.string()
  }))
});

export const LLMProxyRequestSchema = z.object({
  provider: z.enum(["deepseek", "openai", "anthropic", "mistral"]),
  model: z.string(),
  messages: z.array(z.object({
    role: z.enum(["system", "user", "assistant"]),
    content: z.string()
  })),
  response_format: z.enum(["json", "text"]),
  temperature: z.number().min(0).max(1),
  max_tokens: z.number().int(),
  cache_key: z.string().optional()
});

export const LLMProxyResponseSchema = z.object({
  provider_used: z.string(),
  model_used: z.string(),
  output: z.union([z.string(), z.record(z.string(), z.unknown())]),
  token_usage: z.object({
    input: z.number().int(),
    output: z.number().int()
  }),
  cached: z.boolean()
});

export const ErrorEnvelopeSchema = z.object({
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.record(z.string(), z.unknown()).optional(),
    trace_id: UuidSchema,
    retryable: z.boolean()
  })
});

export type CompanyOnboardingRequest = z.infer<typeof CompanyOnboardingRequestSchema>;
export type CompanyOnboardingResponse = z.infer<typeof CompanyOnboardingResponseSchema>;
export type PostGenerateRequest = z.infer<typeof PostGenerateRequestSchema>;
export type PostGenerateResponse = z.infer<typeof PostGenerateResponseSchema>;
export type ScheduleCreateRequest = z.infer<typeof ScheduleCreateRequestSchema>;
export type ScheduleCreateResponse = z.infer<typeof ScheduleCreateResponseSchema>;
export type AnalyticsIngestRequest = z.infer<typeof AnalyticsIngestRequestSchema>;
export type LLMProxyRequest = z.infer<typeof LLMProxyRequestSchema>;
