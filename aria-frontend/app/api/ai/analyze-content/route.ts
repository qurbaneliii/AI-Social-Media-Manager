import { NextResponse } from "next/server";
import { z } from "zod";

import {
  aiPlatformSchema,
  createChatCompletion,
  parseJsonPayload,
  toOpenAIErrorResponse
} from "@/app/api/ai/_lib";

export const dynamic = "force-dynamic";

const analyzeContentSchema = z.object({
  content: z.string().trim().min(1).max(6000),
  platform: aiPlatformSchema
});

const analyzeResponseSchema = z.object({
  scores: z.object({
    engagement: z.number(),
    clarity: z.number(),
    cta_strength: z.number()
  }),
  suggestions: z.array(z.string().min(1)).min(1).max(8)
});

const clampScore = (value: number): number => {
  return Math.max(0, Math.min(100, Math.round(value)));
};

export async function POST(request: Request) {
  try {
    const payload = analyzeContentSchema.parse(await request.json());

    const completion = await createChatCompletion({
      messages: [
        {
          role: "system",
          content:
            "You are a social media quality analyst. Return JSON only with shape: { \"scores\": { \"engagement\": number, \"clarity\": number, \"cta_strength\": number }, \"suggestions\": string[] }. Scores must be 0-100."
        },
        {
          role: "user",
          content: `Platform: ${payload.platform}\n\nContent:\n${payload.content}`
        }
      ],
      max_tokens: 500,
      temperature: 0.3
    });

    const raw = completion.choices[0]?.message?.content ?? "";
    const analysis = parseJsonPayload(raw, analyzeResponseSchema, "OpenAI returned non-JSON analysis payload");

    return NextResponse.json(
      {
        scores: {
          engagement: clampScore(analysis.scores.engagement),
          clarity: clampScore(analysis.scores.clarity),
          cta_strength: clampScore(analysis.scores.cta_strength)
        },
        suggestions: analysis.suggestions
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/analyze-content failed", error);
    return toOpenAIErrorResponse(error, "Failed to analyze content");
  }
}
