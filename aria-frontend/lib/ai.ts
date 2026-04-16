import type { DashboardPlatform } from "@/lib/mock-data";

export interface GeneratePayload {
  platform: DashboardPlatform;
  tone: string;
  topic: string;
  cta: string;
  context?: string;
  brandVocab?: {
    approved: string[];
    banned: string[];
    brandName?: string;
  };
}

interface StreamHandlers {
  onChunk: (chunk: string) => void;
  signal?: AbortSignal;
}

export const streamGeneratedContent = async (payload: GeneratePayload, handlers: StreamHandlers): Promise<void> => {
  const response = await fetch("/api/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    signal: handlers.signal
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Generation failed");
  }

  if (!response.body) {
    throw new Error("Empty streaming response");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const part of parts) {
      const lines = part.split("\n");
      let event = "message";
      let data = "";

      for (const line of lines) {
        if (line.startsWith("event:")) {
          event = line.slice(6).trim();
        }
        if (line.startsWith("data:")) {
          data += line.slice(5).trim();
        }
      }

      if (!data) {
        continue;
      }

      if (event === "error") {
        throw new Error(data);
      }

      if (event === "done") {
        return;
      }

      if (event === "token") {
        handlers.onChunk(data);
      }
    }
  }
};
