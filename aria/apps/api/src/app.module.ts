import { Module } from "@nestjs/common";
import { V1Controller } from "./v1/v1.controller.js";
import { V1Service } from "./v1/v1.service.js";
import { AnalyticsHmacGuard } from "./common/guards/analytics-hmac.guard.js";
import { PrismaService } from "./common/services/prisma.service.js";
import { RedisService } from "./common/services/redis.service.js";
import { S3Service } from "./common/services/s3.service.js";
import { KmsEnvelopeService } from "./common/services/kms-envelope.service.js";

@Module({
  controllers: [V1Controller],
  providers: [V1Service, AnalyticsHmacGuard, PrismaService, RedisService, S3Service, KmsEnvelopeService]
})
export class AppModule {}
