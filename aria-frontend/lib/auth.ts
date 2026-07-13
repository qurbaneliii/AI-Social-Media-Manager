import "server-only";

import jwt from "jsonwebtoken";

import { AUTH_TOKEN_EXPIRY_SECONDS } from "@/lib/auth-constants";
import type { UserRole } from "@/types";

export interface AuthTokenPayload {
  userId: string;
  email: string;
  role: UserRole;
  sub?: string;
  iss?: string;
  aud?: string;
  iat?: number;
  exp?: number;
}

const TOKEN_ISSUER = "aria-frontend";
const TOKEN_AUDIENCE = "aria-api";

const getJwtSecret = (): string => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error("JWT_SECRET is not configured");
  }
  return secret;
};

export const signAuthToken = (payload: Omit<AuthTokenPayload, "iat" | "exp">): string => {
  return jwt.sign(payload, getJwtSecret(), {
    subject: payload.userId,
    issuer: TOKEN_ISSUER,
    audience: TOKEN_AUDIENCE,
    expiresIn: `${AUTH_TOKEN_EXPIRY_SECONDS}s`
  });
};

export const verifyAuthToken = (token: string): AuthTokenPayload | null => {
  try {
    return jwt.verify(token, getJwtSecret(), {
      issuer: TOKEN_ISSUER,
      audience: TOKEN_AUDIENCE,
      algorithms: ["HS256"]
    }) as AuthTokenPayload;
  } catch {
    return null;
  }
};
