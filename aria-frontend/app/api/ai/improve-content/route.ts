import { NextResponse } from "next/server";
import { z } from "zod";

import { fallbackImprove, hasOpenAIKey, toOpenAIErrorResponse } from "@/app/api/ai/_lib";
import { getOpenAIClient } from "@/lib/openai";

export const dynamic = "force-dynamic";

const improveContentSchema = z.object({
  content: z.string().trim().min(1).max(6000),
  instruction: z.string().trim().min(3).max(1000)
});

export async function POST(request: Request) {
  try {
    const payload = improveContentSchema.parse(await request.json());

    if (!hasOpenAIKey()) {
      return NextResponse.json(fallbackImprove(payload.content, payload.instruction), {
        status: 200
      });
    }

    const openai = getOpenAIClient();

    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content:
            "You improve social media content. Keep the original intent, apply the requested instruction, and return only the improved text."
        },
        {
          role: "user",
          content: `Instruction:\n${payload.instruction}\n\nOriginal content:\n${payload.content}`
        }
      ],
      max_tokens: 1000,
      temperature: 0.6
    });

    const improved = completion.choices[0]?.message?.content?.trim() ?? "";
    if (!improved) {
      throw new Error("OpenAI returned empty improved content");
    }

    return NextResponse.json(
      {
        improved
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/improve-content failed", error);
    return toOpenAIErrorResponse(error, "Failed to improve content");
  }
}
