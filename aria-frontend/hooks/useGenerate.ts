"use client";

import { useMemo, useRef, useState } from "react";
import { z } from "zod";

import { streamGeneratedContent, type GeneratePayload } from "@/lib/ai";

export const generateFormSchema = z.object({
  platform: z.enum(["linkedin", "twitter", "instagram"]),
  tone: z.string().min(2),
  topic: z.string().min(3).max(240),
  cta: z.string().min(2),
  context: z.string().max(1500).optional()
});

export type GenerateFormValues = z.infer<typeof generateFormSchema>;

export const useGenerate = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [output, setOutput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const lastPayloadRef = useRef<GeneratePayload | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const hashtags = useMemo(() => {
    const set = new Set<string>();
    const matches = output.match(/#[A-Za-z0-9_]+/g) ?? [];
    for (const tag of matches) {
      set.add(tag);
    }
    return [...set];
  }, [output]);

  const run = async (payload: GeneratePayload) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setOutput("");
    setError(null);
    setIsGenerating(true);
    lastPayloadRef.current = payload;

    try {
      await streamGeneratedContent(payload, {
        signal: controller.signal,
        onChunk: (chunk) => {
          setOutput((prev) => prev + chunk);
        }
      });
    } catch (err) {
      if (controller.signal.aborted) {
        return;
      }
      setError(err instanceof Error ? err.message : "Generation failed");
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerate = async () => {
    if (!lastPayloadRef.current) {
      return;
    }
    await run(lastPayloadRef.current);
  };

  const cancel = () => {
    abortRef.current?.abort();
    setIsGenerating(false);
  };

  return {
    isGenerating,
    output,
    error,
    hashtags,
    run,
    regenerate,
    cancel,
    setOutput
  };
};
