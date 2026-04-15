import "server-only";

import OpenAI from "openai";

let openaiClient: OpenAI | null = null;

export const getOpenAIClient = (): OpenAI => {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is not configured");
  }

  if (openaiClient === null) {
    openaiClient = new OpenAI({ apiKey });
  }

  return openaiClient;
};
