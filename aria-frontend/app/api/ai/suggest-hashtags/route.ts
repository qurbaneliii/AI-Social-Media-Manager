import { NextResponse } from "next/server";
import { z } from "zod";

import {
  aiPlatformSchema,
  safeJsonParse,
  toOpenAIErrorResponse
} from "@/app/api/ai/_lib";
import { openai } from "@/lib/openai";

const suggestHashtagsSchema = z.object({
  content: z.string().trim().min(1).max(6000),
  platform: aiPlatformSchema
});

const hashtagResponseSchema = z.object({
  hashtags: z.array(z.string().min(1)).min(1).max(30)
});

export async function POST(request: Request) {
  try {
    const payload = suggestHashtagsSchema.parse(await request.json());

    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content:
            "Suggest relevant social media hashtags. Return JSON only in shape: { \"hashtags\": string[] }. Do not include # prefix in values."
        },
        {
          role: "user",
          content: `Platform: ${payload.platform}\n\nContent:\n${payload.content}`
        }
      ],
      max_tokens: 300,
      temperature: 0.5
    });

    const raw = completion.choices[0]?.message?.content ?? "";
    const parsed = safeJsonParse<unknown>(raw);
    if (!parsed) {
      throw new Error("OpenAI returned non-JSON hashtag payload");
    }

    const data = hashtagResponseSchema.parse(parsed);
    const hashtags = Array.from(
      new Set(
        data.hashtags
          .map((item) => item.trim().replace(/^#+/, ""))
          .filter((item) => item.length > 0)
      )
    );

    return NextResponse.json(
      {
        hashtags
      },
      { status: 200 }
    );
  } catch (error) {
    console.error("/api/ai/suggest-hashtags failed", error);
    return toOpenAIErrorResponse(error, "Failed to suggest hashtags");
  }
}
