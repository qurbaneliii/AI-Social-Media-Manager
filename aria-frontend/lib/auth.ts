import "server-only";

import jwt from "jsonwebtoken";

import { AUTH_TOKEN_EXPIRY_SECONDS } from "@/lib/auth-constants";
import type { UserRole } from "@/types";

export interface AuthTokenPayload {
  userId: string;
  email: string;
  role: UserRole;
  iat?: number;
  exp?: number;
}

const getJwtSecret = (): string => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error("JWT_SECRET is not configured");
  }
  return secret;
};

export const signAuthToken = (payload: Omit<AuthTokenPayload, "iat" | "exp">): string => {
  return jwt.sign(payload, getJwtSecret(), { expiresIn: `${AUTH_TOKEN_EXPIRY_SECONDS}s` });
};

export const verifyAuthToken = (token: string): AuthTokenPayload | null => {
  try {
    return jwt.verify(token, getJwtSecret()) as AuthTokenPayload;
  } catch {
    return null;
  }
};
