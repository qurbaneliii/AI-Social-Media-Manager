import { NextResponse } from "next/server";
import { z } from "zod";

import {
  generateContentSchema,
  generatePlatformContent,
  toOpenAIErrorResponse
} from "@/app/api/ai/_lib";

export const dynamic = "force-static";

const generateBatchSchema = z.union([
  z.array(generateContentSchema).min(1),
  z.object({
    items: z.array(generateContentSchema).min(1)
  })
]);

export async function POST(request: Request) {
  try {
    const body = generateBatchSchema.parse(await request.json());
    const items = Array.isArray(body) ? body : body.items;

    const settled = await Promise.allSettled(items.map((item) => generatePlatformContent(item)));

    const results = settled.map((entry, index) => {
      const platform = items[index].platform;

      if (entry.status === "fulfilled") {
        return {
          success: true,
          platform,
          content: entry.value
        };
      }

      const reason = entry.reason;
      const message = reason instanceof Error ? reason.message : "Generation failed";
      return {
        success: false,
        platform,
        error: message
      };
    });

    return NextResponse.json(
      {
        results
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/generate-batch failed", error);
    return toOpenAIErrorResponse(error, "Failed to generate batch content");
  }
}
