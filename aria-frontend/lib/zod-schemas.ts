// filename: lib/zod-schemas.ts
// purpose: Form validation schemas matching backend contracts.
// dependencies: zod, types

import { z } from "zod";

import type { CompanyProfileForm, GeneratePostForm, ScheduleRequest } from "@/types";

const isoCodeSchema = z.string().regex(/^[A-Z]{2}$/, "Use ISO-3166-1 alpha-2 code");

const platformSchema = z.enum(["instagram", "linkedin", "facebook", "x", "tiktok", "pinterest"]);
const postIntentSchema = z.enum(["announce", "educate", "promote", "engage", "inspire", "crisis_response"]);
const ctaSchema = z.enum(["learn_more", "book_demo", "buy_now", "download", "comment", "share"]);

export const CompanyProfileSchema: z.ZodType<CompanyProfileForm> = z.object({
  company_name: z.string().min(2).max(120),
  industry_vertical: z.string().min(1),
  target_market: z.object({
    regions: z.array(isoCodeSchema).min(1),
    segments: z.array(z.enum(["B2B", "B2C", "D2C"])) .min(1),
    persona_summary: z.string().min(1)
  }),
  brand_positioning_statement: z.string().min(30).max(500),
  tone_of_voice_descriptors: z.array(z.string().min(1)).min(3).max(20),
  competitor_list: z.array(z.string().min(1)).max(20),
  platform_presence: z.object({
    instagram: z.boolean(),
    linkedin: z.boolean(),
    facebook: z.boolean(),
    x: z.boolean(),
    tiktok: z.boolean(),
    pinterest: z.boolean()
  }),
  posting_frequency_goal: z.object({
    instagram: z.number().min(0).max(21),
    linkedin: z.number().min(0).max(14),
    facebook: z.number().min(0).max(21),
    x: z.number().min(0).max(70),
    tiktok: z.number().min(0).max(21),
    pinterest: z.number().min(0).max(35)
  }),
  primary_cta_types: z.array(ctaSchema).min(1),
  brand_color_hex_codes: z.array(z.string().regex(/^#[0-9A-Fa-f]{6}$/)),
  approved_vocabulary_list: z.array(z.string()),
  banned_vocabulary_list: z.array(z.string()),
  logo_file: z.string().nullable(),
  sample_post_images: z.array(z.string())
});

export const GeneratePostSchema: z.ZodType<GeneratePostForm> = z
  .object({
    company_id: z.string().uuid(),
    post_intent: postIntentSchema,
    core_message: z.string().min(20).max(500),
    target_platforms: z.array(platformSchema).min(1),
    campaign_tag: z.string().optional(),
    attached_media_id: z.string().optional(),
    manual_keywords: z.array(z.string()).optional(),
    urgency_level: z.enum(["scheduled", "immediate"]),
    requested_publish_at: z.string().datetime({ offset: true }).optional()
  })
  .superRefine((value, ctx) => {
    if (value.urgency_level === "scheduled" && !value.requested_publish_at) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["requested_publish_at"],
        message: "requested_publish_at is required for scheduled posts"
      });
    }
  });

export const ScheduleRequestSchema: z.ZodType<ScheduleRequest> = z.object({
  post_id: z.string().uuid(),
  company_id: z.string().uuid(),
  targets: z
    .array(
      z.object({
        platform: platformSchema,
        run_at_utc: z.string().datetime({ offset: true })
      })
    )
    .min(1),
  approval_mode: z.enum(["human", "auto"]),
  manual_override: z
    .object({
      timezone: z.string().min(1),
      force_window: z.boolean()
    })
    .optional()
});

export const VocabularySchema = z.object({
  approved: z.array(z.string()),
  banned: z.array(z.string())
});
