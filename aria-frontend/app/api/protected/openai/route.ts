import { NextResponse } from "next/server";
import { z } from "zod";

import { openai } from "@/lib/openai";

const promptSchema = z.object({
  prompt: z.string().min(1).max(4000)
});

export async function POST(request: Request) {
  try {
    const payload = promptSchema.parse(await request.json());

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: payload.prompt }],
      temperature: 0.7
    });

    const text = completion.choices[0]?.message?.content ?? "";
    return NextResponse.json({ text }, { status: 200 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({ error: "Invalid input", details: error.flatten() }, { status: 400 });
    }
    return NextResponse.json({ error: "OpenAI request failed" }, { status: 500 });
  }
}
