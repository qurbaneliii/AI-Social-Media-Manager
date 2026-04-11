// filename: components/ui/LLMProviderBadge.tsx
// purpose: Model provider badge with fallback handling.

"use client";

interface Props {
  provider: "openai" | "anthropic" | string;
}

export const LLMProviderBadge = ({ provider }: Props) => {
  if (provider === "openai") {
    return <span className="rounded-full bg-cyan-100 px-3 py-1 text-xs font-medium text-cyan-700">OpenAI</span>;
  }
  if (provider === "anthropic") {
    return <span className="rounded-full bg-violet-100 px-3 py-1 text-xs font-medium text-violet-700">Anthropic</span>;
  }
  return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">Unknown</span>;
};
