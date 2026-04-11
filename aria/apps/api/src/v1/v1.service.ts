import { Injectable, ConflictException, NotFoundException, BadRequestException } from "@nestjs/common";
import { randomUUID } from "node:crypto";
import {
  AnalyticsIngestRequestSchema,
  AnalyticsIngestResponseSchema,
  CompanyOnboardingRequestSchema,
  CompanyOnboardingResponseSchema,
  LLMProxyRequestSchema,
  LLMProxyResponseSchema,
  MediaPresignRequestSchema,
  MediaPresignResponseSchema,
  PostGenerateRequestSchema,
  PostGenerateResponseSchema,
  PublishNowRequestSchema,
  PublishResponseSchema,
  ScheduleCreateRequestSchema,
  ScheduleCreateResponseSchema
} from "@aria/types";
import { PrismaService } from "../common/services/prisma.service.js";
import { CacheTTLClass, RedisService } from "../common/services/redis.service.js";
import { S3Service } from "../common/services/s3.service.js";

@Injectable()
export class V1Service {
  constructor(
    private readonly prisma: PrismaService,
    private readonly s3: S3Service,
    private readonly redis: RedisService
  ) {}

  async submitCompanyProfile(payload: unknown) {
    const parsed = CompanyOnboardingRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    const company = await this.prisma.company.create({
      data: {
        tenantId: randomUUID(),
        name: parsed.data.company_name,
        industryVertical: parsed.data.industry_vertical,
        targetMarketJson: parsed.data.target_market,
        platformPresenceJson: parsed.data.platform_presence,
        postingFrequencyGoalJson: parsed.data.posting_frequency_goal
      }
    });

    await this.prisma.brandProfile.create({
      data: {
        tenantId: company.tenantId,
        companyId: company.id,
        profileVersion: 1,
        brandPositioningStatement: parsed.data.brand_positioning_statement,
        toneOfVoiceDescriptors: parsed.data.tone_of_voice_descriptors,
        competitorList: parsed.data.competitor_list,
        primaryCtaTypes: parsed.data.primary_cta_types,
        brandColorHexCodes: parsed.data.brand_color_hex_codes,
        approvedVocabularyList: parsed.data.approved_vocabulary_list,
        bannedVocabularyList: parsed.data.banned_vocabulary_list
      }
    });

    const response = {
      company_id: company.id,
      profile_version: 1,
      status: "submitted"
    };
    return CompanyOnboardingResponseSchema.parse(response);
  }

  async createMediaPresign(payload: unknown) {
    const parsed = MediaPresignRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    if (parsed.data.size_bytes > 25 * 1024 * 1024) {
      throw new BadRequestException("File exceeds maximum allowed size (25MB)");
    }

    if (!/^image\//.test(parsed.data.mime_type) && !/^video\//.test(parsed.data.mime_type)) {
      throw new BadRequestException("Unsupported MIME type");
    }

    const presigned = await this.s3.presignUpload(parsed.data.file_name, parsed.data.mime_type);

    await this.prisma.mediaAsset.create({
      data: {
        id: presigned.mediaId,
        tenantId: randomUUID(),
        companyId: parsed.data.company_id,
        s3Key: presigned.s3Key,
        mimeType: parsed.data.mime_type,
        sizeBytes: BigInt(parsed.data.size_bytes),
        status: "uploaded",
        uploadedAt: new Date()
      }
    });

    return MediaPresignResponseSchema.parse({
      media_id: presigned.mediaId,
      upload_url: presigned.uploadUrl,
      s3_key: presigned.s3Key
    });
  }

  async generatePost(payload: unknown) {
    const parsed = PostGenerateRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    const post = await this.prisma.post.create({
      data: {
        tenantId: randomUUID(),
        companyId: parsed.data.company_id,
        postIntent: parsed.data.post_intent,
        coreMessage: parsed.data.core_message,
        targetPlatforms: parsed.data.target_platforms,
        campaignTag: parsed.data.campaign_tag,
        attachedMediaId: parsed.data.attached_media_id,
        manualKeywords: parsed.data.manual_keywords,
        urgencyLevel: parsed.data.urgency_level,
        requestedPublishAt: parsed.data.requested_publish_at ? new Date(parsed.data.requested_publish_at) : null,
        status: "generating"
      }
    });

    return PostGenerateResponseSchema.parse({
      post_id: post.id,
      status: "generating",
      estimated_ready_seconds: 30
    });
  }

  async getGenerationResult(postId: string) {
    const post = await this.prisma.post.findUnique({
      where: { id: postId },
      include: { variants: true }
    });
    if (!post) throw new NotFoundException("Post not found");
    return {
      post_id: post.id,
      status: post.status,
      generated_package: post.generatedPackageJson,
      variants: post.variants
    };
  }

  async createSchedules(payload: unknown) {
    const parsed = ScheduleCreateRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    const scheduleIds: string[] = [];

    for (const target of parsed.data.targets) {
      const existing = await this.prisma.schedule.findFirst({
        where: {
          companyId: parsed.data.company_id,
          platform: target.platform,
          runAtUtc: new Date(target.run_at_utc)
        }
      });

      if (existing) {
        throw new ConflictException("Schedule conflict for platform and run_at_utc");
      }

      const created = await this.prisma.schedule.create({
        data: {
          tenantId: randomUUID(),
          companyId: parsed.data.company_id,
          postId: parsed.data.post_id,
          platform: target.platform,
          runAtUtc: new Date(target.run_at_utc),
          approvalMode: parsed.data.approval_mode,
          status: "queued",
          idempotencyKey: randomUUID(),
          timezone: parsed.data.manual_override.timezone,
          forceWindow: parsed.data.manual_override.force_window
        }
      });
      scheduleIds.push(created.id);
    }

    return ScheduleCreateResponseSchema.parse({
      schedule_ids: scheduleIds,
      status: "queued"
    });
  }

  async approveSchedule(scheduleId: string) {
    const schedule = await this.prisma.schedule.findUnique({ where: { id: scheduleId } });
    if (!schedule) throw new NotFoundException("Schedule not found");

    const updated = await this.prisma.schedule.update({
      where: { id: scheduleId },
      data: { status: "approved" }
    });

    return {
      schedule_id: updated.id,
      status: updated.status
    };
  }

  async publishNow(payload: unknown) {
    const parsed = PublishNowRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    return PublishResponseSchema.parse({
      status: "published",
      external_post_id: `ext_${randomUUID()}`
    });
  }

  async ingestAnalytics(payload: unknown) {
    const parsed = AnalyticsIngestRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    let ingestedCount = 0;
    const errors: Array<{ index: number; reason: string }> = [];

    for (const [index, record] of parsed.data.records.entries()) {
      try {
        const post = await this.prisma.post.findUnique({ where: { id: record.post_id } });
        if (!post) {
          throw new Error("Post not found for record");
        }

        await this.prisma.performanceMetric.create({
          data: {
            tenantId: post.tenantId,
            companyId: post.companyId,
            postId: record.post_id,
            platform: record.platform as never,
            externalPostId: record.external_post_id,
            impressions: record.impressions,
            reach: record.reach,
            engagementRate: record.engagement_rate,
            clickThroughRate: record.click_through_rate,
            saves: record.saves,
            shares: record.shares,
            followerGrowthDelta: record.follower_growth_delta,
            postingTimestamp: new Date(record.posting_timestamp),
            capturedAt: new Date(record.captured_at),
            source: "manual"
          }
        });
        ingestedCount += 1;
      } catch (error) {
        errors.push({ index, reason: (error as Error).message });
      }
    }

    return AnalyticsIngestResponseSchema.parse({
      ingested_count: ingestedCount,
      rejected_count: errors.length,
      errors
    });
  }

  async llmProxy(payload: unknown) {
    const parsed = LLMProxyRequestSchema.safeParse(payload);
    if (!parsed.success) throw new BadRequestException(parsed.error.flatten());

    const cacheKey = parsed.data.cache_key ? `llm:${parsed.data.cache_key}` : "";
    if (cacheKey) {
      const cached = await this.redis.getJson<unknown>(cacheKey);
      if (cached) {
        return LLMProxyResponseSchema.parse(cached);
      }
    }

    const output = parsed.data.response_format === "json"
      ? { text: "generated" }
      : "generated";

    const response = LLMProxyResponseSchema.parse({
      provider_used: parsed.data.provider,
      model_used: parsed.data.model,
      output,
      token_usage: { input: 128, output: 256 },
      cached: false
    });

    if (cacheKey) {
      await this.redis.setJson(cacheKey, response, CacheTTLClass.MEDIUM);
    }

    return response;
  }

  getOauthConnect(platform: string, state: string) {
    const authorizationUrl = `https://auth.${platform}.com/oauth/authorize?state=${encodeURIComponent(state)}&response_type=code`;
    return { authorization_url: authorizationUrl };
  }

  handleOauthCallback(platform: string, code: string, state: string) {
    if (!code || !state) {
      throw new BadRequestException("Missing OAuth code or state");
    }

    return {
      platform,
      connected: true,
      code,
      state
    };
  }
}
