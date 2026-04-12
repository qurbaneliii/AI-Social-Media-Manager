import { jwtVerify } from "jose";
import { NextRequest, NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth-constants";

const getTokenFromRequest = (request: NextRequest): string | null => {
  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Bearer ")) {
    const value = authHeader.slice(7).trim();
    if (value) {
      return value;
    }
  }

  return request.cookies.get(AUTH_COOKIE_NAME)?.value ?? null;
};

export async function middleware(request: NextRequest) {
  const token = getTokenFromRequest(request);
  const secret = process.env.JWT_SECRET;

  if (!token || !secret) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    await jwtVerify(token, new TextEncoder().encode(secret));
    return NextResponse.next();
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export const config = {
  matcher: ["/api/protected/:path*"]
};
