import OpenAI from "openai";
import { NextResponse } from "next/server";
import { z } from "zod";

import { openai } from "@/lib/openai";

export const aiPlatformSchema = z.enum([
  "linkedin",
  "twitter",
  "instagram",
  "facebook",
  "tiktok",
  "pinterest"
]);

export const ctaTypeSchema = z.enum([
  "learn_more",
  "book_demo",
  "buy_now",
  "download",
  "comment",
  "share"
]);

export type AIPlatform = z.infer<typeof aiPlatformSchema>;

const PLATFORM_CHAR_LIMITS: Record<AIPlatform, number> = {
  linkedin: 3000,
  twitter: 280,
  instagram: 2200,
  facebook: 63206,
  tiktok: 2200,
  pinterest: 500
};

export const generateContentSchema = z.object({
  platform: aiPlatformSchema,
  topic: z.string().trim().min(3).max(2000),
  tone: z.string().trim().min(2).max(300),
  ctaType: ctaTypeSchema,
  brandColors: z.array(z.string()).max(20),
  approvedVocabulary: z.array(z.string()).max(200),
  bannedVocabulary: z.array(z.string()).max(200),
  postingFrequency: z.number().int().nonnegative().optional(),
  companyProfile: z.record(z.string(), z.unknown()).optional()
});

export type GenerateContentInput = z.infer<typeof generateContentSchema>;

const stringifyList = (items: string[]): string => {
  if (!items.length) {
    return "none";
  }
  return items.join(", ");
};

const includesBannedVocabulary = (content: string, bannedVocabulary: string[]): boolean => {
  const lowered = content.toLowerCase();
  return bannedVocabulary.some((item) => item.trim().length > 0 && lowered.includes(item.toLowerCase()));
};

const buildSystemPrompt = (input: GenerateContentInput): string => {
  const charLimit = PLATFORM_CHAR_LIMITS[input.platform];
  const postingFrequencyText =
    typeof input.postingFrequency === "number" ? `${input.postingFrequency} posts/week` : "not provided";

  return [
    "You are ARIA CONSOLE, an expert social media copywriter.",
    `Write one post for ${input.platform}.`,
    `Hard max length: ${charLimit} characters. Never exceed this.`,
    `Tone requirement: ${input.tone}.`,
    `CTA requirement: end the post with a clear ${input.ctaType} call-to-action.`,
    `Brand colors for context: ${stringifyList(input.brandColors)}.`,
    `Posting frequency goal: ${postingFrequencyText}.`,
    `Approved vocabulary (use where relevant): ${stringifyList(input.approvedVocabulary)}.`,
    `Banned vocabulary (never use): ${stringifyList(input.bannedVocabulary)}.`,
    "Output only the final post text without markdown fences or commentary.",
    input.companyProfile ? `Company profile context: ${JSON.stringify(input.companyProfile)}` : ""
  ]
    .filter(Boolean)
    .join("\n");
};

export const safeJsonParse = <T>(rawText: string): T | null => {
  const text = rawText.trim();
  const normalized = text.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/i, "");

  try {
    return JSON.parse(normalized) as T;
  } catch {
    const start = normalized.indexOf("{");
    const end = normalized.lastIndexOf("}");
    if (start >= 0 && end > start) {
      try {
        return JSON.parse(normalized.slice(start, end + 1)) as T;
      } catch {
        return null;
      }
    }
    return null;
  }
};

export const toOpenAIErrorResponse = (error: unknown, fallbackMessage: string): NextResponse => {
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      {
        error: "Invalid request body",
        details: error.flatten()
      },
      { status: 400 }
    );
  }

  if (error instanceof OpenAI.APIError) {
    const status = error.status ?? 500;
    return NextResponse.json(
      {
        error: error.message || fallbackMessage
      },
      { status }
    );
  }

  if (error instanceof Error) {
    return NextResponse.json(
      {
        error: error.message || fallbackMessage
      },
      { status: 500 }
    );
  }

  return NextResponse.json(
    {
      error: fallbackMessage
    },
    { status: 500 }
  );
};

export const generatePlatformContent = async (input: GenerateContentInput): Promise<string> => {
  const systemPrompt = buildSystemPrompt(input);

  const response = await openai.chat.completions.create({
    model: "gpt-4o",
    messages: [
      { role: "system", content: systemPrompt },
      {
        role: "user",
        content: `Topic: ${input.topic}\nWrite a platform-native post that strictly follows all constraints.`
      }
    ],
    max_tokens: 1000,
    temperature: 0.7
  });

  let content = response.choices[0]?.message?.content?.trim() ?? "";
  if (!content) {
    throw new Error("OpenAI returned empty content");
  }

  if (includesBannedVocabulary(content, input.bannedVocabulary)) {
    const rewritten = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content:
            "Rewrite the provided post while keeping meaning and tone, but remove banned vocabulary entirely and preserve platform limits."
        },
        {
          role: "user",
          content: `Original post:\n${content}\n\nBanned words:\n${stringifyList(input.bannedVocabulary)}\n\nPlatform:\n${input.platform}`
        }
      ],
      max_tokens: 1000,
      temperature: 0.4
    });

    content = rewritten.choices[0]?.message?.content?.trim() ?? content;
  }

  if (includesBannedVocabulary(content, input.bannedVocabulary)) {
    throw new Error("Generated content still contains banned vocabulary after rewrite");
  }

  const maxCharacters = PLATFORM_CHAR_LIMITS[input.platform];
  if (content.length > maxCharacters) {
    content = content.slice(0, maxCharacters).trim();
  }

  return content;
};
