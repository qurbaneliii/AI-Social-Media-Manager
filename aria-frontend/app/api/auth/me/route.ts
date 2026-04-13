import { NextRequest, NextResponse } from "next/server";

import { verifyAuthToken } from "@/lib/auth";
import { AUTH_COOKIE_NAME } from "@/lib/auth-constants";
import { prisma } from "@/lib/prisma";

const getBearerToken = (authorizationHeader: string | null): string | null => {
  if (!authorizationHeader || !authorizationHeader.startsWith("Bearer ")) {
    return null;
  }
  return authorizationHeader.slice(7).trim() || null;
};

export async function GET(request: NextRequest) {
  const authorizationHeader = request.headers.get("authorization");
  const bearerToken = getBearerToken(authorizationHeader);
  const cookieToken = request.cookies.get(AUTH_COOKIE_NAME)?.value ?? null;

  const token = bearerToken ?? cookieToken;
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const decoded = verifyAuthToken(token);
  if (!decoded) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const user = await prisma.user.findUnique({
    where: { id: decoded.userId },
    select: {
      id: true,
      name: true,
      email: true,
      role: true,
      createdAt: true,
    }
  });

  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  return NextResponse.json({ user }, { status: 200 });
}
