import { NextResponse } from "next/server";
import { z } from "zod";

import {
  aiPlatformSchema,
  fallbackTopics,
  hasOpenAIKey,
  safeJsonParse,
  toOpenAIErrorResponse
} from "@/app/api/ai/_lib";
import { getOpenAIClient } from "@/lib/openai";

export const dynamic = "force-dynamic";

const suggestTopicsSchema = z.object({
  industry: z.string().trim().min(2).max(300),
  platforms: z.array(aiPlatformSchema).min(1).max(6),
  companyProfile: z.record(z.string(), z.unknown())
});

const topicsResponseSchema = z.object({
  topics: z.array(z.string().min(3)).min(5).max(12)
});

export async function POST(request: Request) {
  try {
    const payload = suggestTopicsSchema.parse(await request.json());

    if (!hasOpenAIKey()) {
      return NextResponse.json(fallbackTopics(payload.industry), { status: 200 });
    }

    const openai = getOpenAIClient();

    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content:
            "You are a social media strategist. Suggest content topics and return JSON only in this shape: { \"topics\": string[] }. Provide concise, practical topics."
        },
        {
          role: "user",
          content: `Industry: ${payload.industry}\nPlatforms: ${payload.platforms.join(", ")}\nCompany profile: ${JSON.stringify(payload.companyProfile)}\n\nReturn exactly 5 topic suggestions.`
        }
      ],
      max_tokens: 400,
      temperature: 0.7
    });

    const raw = completion.choices[0]?.message?.content ?? "";
    const parsed = safeJsonParse<unknown>(raw);
    if (!parsed) {
      throw new Error("OpenAI returned non-JSON topics payload");
    }

    const data = topicsResponseSchema.parse(parsed);
    const topics = data.topics.slice(0, 5);

    return NextResponse.json(
      {
        topics
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/suggest-topics failed", error);
    return toOpenAIErrorResponse(error, "Failed to suggest topics");
  }
}
