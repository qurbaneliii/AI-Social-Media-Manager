import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import { createRemoteJWKSet, jwtVerify, type JWTPayload } from "jose";
import { env } from "../../config/env.js";

declare module "fastify" {
  interface FastifyRequest {
    auth?: JWTPayload;
  }
}

@Injectable()
export class JwtGuard implements CanActivate {
  private jwks = createRemoteJWKSet(new URL(`https://${env.auth0Domain}/.well-known/jwks.json`));

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const authHeader = request.headers.authorization as string | undefined;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      throw new UnauthorizedException("Missing bearer token");
    }

    const token = authHeader.slice("Bearer ".length).trim();

    const { payload } = await jwtVerify(token, this.jwks, {
      issuer: env.auth0Issuer,
      audience: env.auth0Audience
    });

    request.auth = payload;
    return true;
  }
}
