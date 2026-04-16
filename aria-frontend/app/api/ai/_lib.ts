import OpenAI from "openai";
import { NextResponse } from "next/server";
import { z } from "zod";

import { getOpenAIClient } from "@/lib/openai";

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

const parseIntegerEnv = (raw: string | undefined, fallback: number, minimum: number): number => {
  if (!raw) {
    return fallback;
  }

  const parsed = Number.parseInt(raw, 10);
  if (Number.isNaN(parsed)) {
    return fallback;
  }

  return Math.max(minimum, parsed);
};

const OPENAI_MODEL = process.env.OPENAI_MODEL ?? "gpt-4o-mini";
const OPENAI_TIMEOUT_MS = parseIntegerEnv(process.env.OPENAI_REQUEST_TIMEOUT_MS, 45000, 1000);
const OPENAI_MAX_RETRIES = parseIntegerEnv(process.env.OPENAI_MAX_RETRIES, 2, 0);

const RETRYABLE_STATUS = new Set([408, 409, 429, 500, 502, 503, 504]);

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

const sleep = async (ms: number) => {
  await new Promise((resolve) => setTimeout(resolve, ms));
};

const sanitizeText = (input: string, maxChars: number): string => {
  return input
    .replace(/[\u0000-\u001F\u007F]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxChars);
};

const sanitizeList = (items: string[], maxItemChars: number, maxItems: number): string[] => {
  return items
    .map((item) => sanitizeText(item, maxItemChars))
    .filter((item) => item.length > 0)
    .slice(0, maxItems);
};

const sanitizeCompanyProfile = (value: Record<string, unknown> | undefined): string => {
  if (!value) {
    return "";
  }

  try {
    return JSON.stringify(value).slice(0, 5000);
  } catch {
    return "";
  }
};

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
  const topic = sanitizeText(input.topic, 2000);
  const tone = sanitizeText(input.tone, 300);
  const approvedVocabulary = sanitizeList(input.approvedVocabulary, 120, 200);
  const bannedVocabulary = sanitizeList(input.bannedVocabulary, 120, 200);
  const brandColors = sanitizeList(input.brandColors, 40, 20);
  const companyProfile = sanitizeCompanyProfile(input.companyProfile);

  const charLimit = PLATFORM_CHAR_LIMITS[input.platform];
  const postingFrequencyText =
    typeof input.postingFrequency === "number" ? `${input.postingFrequency} posts/week` : "not provided";

  return [
    "You are ARIA CONSOLE, an expert social media copywriter.",
    `Write one post for ${input.platform}.`,
    `Topic: ${topic}.`,
    `Hard max length: ${charLimit} characters. Never exceed this.`,
    `Tone requirement: ${tone}.`,
    `CTA requirement: end the post with a clear ${input.ctaType} call-to-action.`,
    `Brand colors for context: ${stringifyList(brandColors)}.`,
    `Posting frequency goal: ${postingFrequencyText}.`,
    `Approved vocabulary (use where relevant): ${stringifyList(approvedVocabulary)}.`,
    `Banned vocabulary (never use): ${stringifyList(bannedVocabulary)}.`,
    "Output only the final post text without markdown fences or commentary.",
    companyProfile ? `Company profile context: ${companyProfile}` : ""
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

  if (error instanceof Error && error.message.includes("OPENAI_API_KEY is not configured")) {
    return NextResponse.json(
      {
        error: "OPENAI_API_KEY is not configured"
      },
      { status: 503 }
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

const shouldRetryOpenAI = (error: unknown): boolean => {
  if (error instanceof OpenAI.APIError) {
    return RETRYABLE_STATUS.has(error.status ?? 500);
  }

  if (error instanceof Error) {
    const message = error.message.toLowerCase();
    return message.includes("timeout") || message.includes("network") || message.includes("econn") || message.includes("reset");
  }

  return false;
};

type ChatCreateParams = Omit<OpenAI.Chat.Completions.ChatCompletionCreateParamsNonStreaming, "model"> & {
  model?: string;
};

export const createChatCompletion = async (
  params: ChatCreateParams
): Promise<OpenAI.Chat.Completions.ChatCompletion> => {
  const openai = getOpenAIClient();

  const effectiveParams: OpenAI.Chat.Completions.ChatCompletionCreateParamsNonStreaming = {
    ...params,
    model: params.model ?? OPENAI_MODEL
  };

  let attempt = 0;
  for (;;) {
    try {
      return await openai.chat.completions.create(effectiveParams, {
        timeout: OPENAI_TIMEOUT_MS
      });
    } catch (error) {
      if (attempt >= OPENAI_MAX_RETRIES || !shouldRetryOpenAI(error)) {
        throw error;
      }

      const delay = Math.min(1200 * (2 ** attempt), 8000);
      await sleep(delay);
      attempt += 1;
    }
  }
};

export const parseJsonPayload = <T>(raw: string, schema: z.ZodType<T>, errorMessage: string): T => {
  const parsed = safeJsonParse<unknown>(raw);
  if (!parsed) {
    throw new Error(errorMessage);
  }

  return schema.parse(parsed);
};

export const generatePlatformContent = async (input: GenerateContentInput): Promise<string> => {
  const systemPrompt = buildSystemPrompt(input);

  const response = await createChatCompletion({
    messages: [
      { role: "system", content: systemPrompt },
      {
        role: "user",
        content: `Topic: ${sanitizeText(input.topic, 2000)}\nWrite a platform-native post that strictly follows all constraints.`
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
    const rewritten = await createChatCompletion({
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
