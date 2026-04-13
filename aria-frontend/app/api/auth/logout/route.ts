import { NextResponse } from "next/server";

import { AUTH_COOKIE_NAME } from "@/lib/auth-constants";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

export async function POST() {
  if (isStatic) {
    return NextResponse.json({ message: "Preview mode" }, { status: 200 });
  }

  const response = NextResponse.json({ message: "Logged out" }, { status: 200 });
  response.cookies.set({
    name: AUTH_COOKIE_NAME,
    value: "",
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0,
    path: "/"
  });
  return response;
}
