import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import { createHmac, timingSafeEqual } from "node:crypto";

@Injectable()
export class AnalyticsHmacGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers["x-api-key"] as string | undefined;
    const signature = request.headers["x-signature"] as string | undefined;

    const expectedApiKey = process.env.ANALYTICS_INGEST_API_KEY ?? "";
    const secret = process.env.WEBHOOK_HMAC_SECRET ?? "";

    if (!apiKey || apiKey !== expectedApiKey) {
      throw new UnauthorizedException("Invalid API key");
    }

    if (!signature || !secret) {
      throw new UnauthorizedException("Missing signature or HMAC secret");
    }

    const raw = JSON.stringify(request.body ?? {});
    const computed = createHmac("sha256", secret).update(raw).digest("hex");
    const provided = signature.replace(/^sha256=/, "");

    const a = Buffer.from(computed, "utf8");
    const b = Buffer.from(provided, "utf8");

    if (a.length !== b.length || !timingSafeEqual(a, b)) {
      throw new UnauthorizedException("Invalid HMAC signature");
    }

    return true;
  }
}
