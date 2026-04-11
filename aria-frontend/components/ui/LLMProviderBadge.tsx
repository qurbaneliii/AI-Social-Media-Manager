// filename: components/ui/LLMProviderBadge.tsx
// purpose: Model provider badge with fallback handling.

"use client";

interface Props {
  provider?: string;
  providerUsed?: string;
  cached?: boolean;
}

export const LLMProviderBadge = ({ provider, providerUsed, cached = false }: Props) => {
  if (cached) {
    return <span className="rounded-full bg-teal-100 px-3 py-1 text-xs font-medium text-teal-700">Served from cache</span>;
  }

  const resolvedProvider = (providerUsed ?? provider ?? "unknown").toLowerCase();

  if (resolvedProvider === "openai") {
    return <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">OpenAI</span>;
  }
  if (resolvedProvider === "anthropic") {
    return <span className="rounded-full bg-orange-100 px-3 py-1 text-xs font-medium text-orange-700">Anthropic</span>;
  }
  if (resolvedProvider === "deepseek") {
    return <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">DeepSeek</span>;
  }
  if (resolvedProvider === "mistral") {
    return <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-700">Mistral</span>;
  }
  return <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">{providerUsed ?? provider ?? "Unknown"}</span>;
};
