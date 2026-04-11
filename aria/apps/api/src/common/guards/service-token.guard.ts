import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import { env } from "../../config/env.js";

@Injectable()
export class ServiceTokenGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const token = request.headers["x-service-token"] as string | undefined;
    if (!token || token !== env.serviceToken) {
      throw new UnauthorizedException("Invalid service token");
    }
    return true;
  }
}
