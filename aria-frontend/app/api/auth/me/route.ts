import { NextResponse } from "next/server";

export const dynamic = "force-static";

export async function GET() {
  return NextResponse.json(
    {
      error: "Authentication requires a live server. Preview mode is enabled."
    },
    { status: 401 }
  );
}
