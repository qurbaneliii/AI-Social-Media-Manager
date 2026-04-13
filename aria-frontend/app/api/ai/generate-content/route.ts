import { NextResponse } from "next/server";

import { generateContentSchema, generatePlatformContent, toOpenAIErrorResponse } from "@/app/api/ai/_lib";

export async function POST(request: Request) {
  try {
    const payload = generateContentSchema.parse(await request.json());
    const content = await generatePlatformContent(payload);

    return NextResponse.json(
      {
        content,
        platform: payload.platform
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/generate-content failed", error);
    return toOpenAIErrorResponse(error, "Failed to generate content");
  }
}
