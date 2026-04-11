import {
  Body,
  Controller,
  Get,
  Param,
  Post,
  Query,
  UseGuards
} from "@nestjs/common";
import { randomUUID } from "node:crypto";
import { AnalyticsHmacGuard } from "../common/guards/analytics-hmac.guard.js";
import { JwtGuard } from "../common/guards/jwt.guard.js";
import { ServiceTokenGuard } from "../common/guards/service-token.guard.js";
import { V1Service } from "./v1.service.js";

@Controller("v1")
export class V1Controller {
  constructor(private readonly service: V1Service) {}

  @UseGuards(JwtGuard)
  @Post("onboarding/company-profile")
  async onboarding(@Body() body: unknown) {
    return this.service.submitCompanyProfile(body);
  }

  @UseGuards(JwtGuard)
  @Post("media/presign")
  async mediaPresign(@Body() body: unknown) {
    return this.service.createMediaPresign(body);
  }

  @UseGuards(JwtGuard)
  @Post("posts/generate")
  async postGenerate(@Body() body: unknown) {
    return this.service.generatePost(body);
  }

  @UseGuards(JwtGuard)
  @Get("posts/:post_id/generation-result")
  async generationResult(@Param("post_id") postId: string) {
    return this.service.getGenerationResult(postId);
  }

  @UseGuards(JwtGuard)
  @Post("schedules")
  async schedules(@Body() body: unknown) {
    return this.service.createSchedules(body);
  }

  @UseGuards(JwtGuard)
  @Post("schedules/:schedule_id/approve")
  async approve(@Param("schedule_id") scheduleId: string) {
    return this.service.approveSchedule(scheduleId);
  }

  @UseGuards(JwtGuard)
  @Post("platform/publish-now")
  async publishNow(@Body() body: unknown) {
    return this.service.publishNow(body);
  }

  @UseGuards(AnalyticsHmacGuard)
  @Post("analytics/ingest")
  async ingestAnalytics(@Body() body: unknown) {
    return this.service.ingestAnalytics(body);
  }

  @UseGuards(ServiceTokenGuard)
  @Post("llm/proxy/chat")
  async llmProxy(@Body() body: unknown) {
    return this.service.llmProxy(body);
  }

  @UseGuards(JwtGuard)
  @Get("platform/oauth/:platform/connect")
  async oauthConnect(@Param("platform") platform: string, @Query("state") state = "") {
    return this.service.getOauthConnect(platform, state || randomUUID());
  }

  @Get("platform/oauth/:platform/callback")
  async oauthCallback(
    @Param("platform") platform: string,
    @Query("code") code = "",
    @Query("state") state = ""
  ) {
    return this.service.handleOauthCallback(platform, code, state);
  }
}
