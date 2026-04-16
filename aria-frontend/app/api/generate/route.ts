import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";

export const dynamic = "force-dynamic";

const requestSchema = z.object({
  platform: z.enum(["linkedin", "twitter", "instagram"]),
  tone: z.string().min(2).max(120),
  topic: z.string().min(3).max(600),
  cta: z.string().min(2).max(80),
  context: z.string().max(1600).optional(),
  brandVocab: z
    .object({
      approved: z.array(z.string()).default([]),
      banned: z.array(z.string()).default([]),
      brandName: z.string().optional()
    })
    .optional()
});

type GenerateRequest = z.infer<typeof requestSchema>;

const platformRules: Record<GenerateRequest["platform"], string> = {
  linkedin: "LinkedIn: professional, 150-300 words, 3-5 hashtags, clear line breaks.",
  twitter: "Twitter: punchy, max 250 characters, 2-3 hashtags, hook in first line.",
  instagram: "Instagram: engaging and emoji-friendly, 5-10 hashtags, light storytelling."
};

const buildSystemPrompt = (payload: GenerateRequest): string => {
  const approved = payload.brandVocab?.approved?.join(", ") || "none";
  const banned = payload.brandVocab?.banned?.join(", ") || "none";
  const brandName = payload.brandVocab?.brandName || "ARIA Brand";

  return [
    "You are ARIA, an expert social media manager AI.",
    `Brand: ${brandName}`,
    `Platform: ${payload.platform}`,
    `Tone: ${payload.tone}`,
    `Approved vocabulary: ${approved}`,
    `Banned vocabulary: ${banned}`,
    "Rules:",
    platformRules[payload.platform],
    "Return ONLY the post text, no explanations."
  ].join("\n");
};

const buildUserPrompt = (payload: GenerateRequest): string => {
  return [
    `Generate a ${payload.platform} post about: ${payload.topic}`,
    `CTA: ${payload.cta}`,
    `Additional context: ${payload.context || "none"}`
  ].join("\n");
};

const sseHeaders = {
  "Content-Type": "text/event-stream; charset=utf-8",
  Connection: "keep-alive",
  "Cache-Control": "no-cache, no-transform"
};

const writeEvent = (controller: ReadableStreamDefaultController, encoder: TextEncoder, event: string, data: string) => {
  const lines = data.split(/\r?\n/).map((line) => `data: ${line}`).join("\n");
  controller.enqueue(encoder.encode(`event: ${event}\n${lines}\n\n`));
};

const getErrorMessage = (error: unknown): string => {
  if (error instanceof Anthropic.APIError) {
    if (error.status === 429) {
      return "Rate limit reached. Please retry in a moment.";
    }
    return error.message || "Anthropic API error";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Generation failed";
};

export async function POST(request: Request): Promise<Response> {
  let payload: GenerateRequest;

  try {
    payload = requestSchema.parse(await request.json());
  } catch (error) {
    const message = error instanceof Error ? error.message : "Invalid request payload";
    return new Response(message, { status: 400 });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response("ANTHROPIC_API_KEY is not configured", { status: 503 });
  }

  const anthropic = new Anthropic({ apiKey });
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        console.info("/api/generate request", {
          platform: payload.platform,
          topic: payload.topic.slice(0, 90)
        });

        const response = await anthropic.messages.create({
          model: "claude-sonnet-4-20250514",
          max_tokens: 900,
          temperature: 0.7,
          stream: true,
          system: buildSystemPrompt(payload),
          messages: [{ role: "user", content: buildUserPrompt(payload) }]
        });

        for await (const event of response) {
          if (event.type === "content_block_delta" && event.delta.type === "text_delta") {
            writeEvent(controller, encoder, "token", event.delta.text);
          }
        }

        writeEvent(controller, encoder, "done", "ok");
      } catch (error) {
        writeEvent(controller, encoder, "error", getErrorMessage(error));
      } finally {
        controller.close();
      }
    }
  });

  return new Response(stream, { headers: sseHeaders });
}
