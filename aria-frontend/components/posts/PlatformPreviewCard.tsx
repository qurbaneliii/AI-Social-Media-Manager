// filename: components/posts/PlatformPreviewCard.tsx
// purpose: Platform-specific post preview with char-limit feedback.

"use client";

import { PLATFORM_CHAR_LIMITS } from "@/config/constants";
import type { Platform, PostVariant } from "@/types";

interface Props {
  platform: Platform;
  variant: PostVariant;
  charLimit?: number;
  imageUrl?: string | null;
  hashtags?: string[];
  ctaText?: string | null;
}

export const PlatformPreviewCard = ({ platform, variant, charLimit, imageUrl, hashtags = [], ctaText }: Props) => {
  const limit = charLimit ?? PLATFORM_CHAR_LIMITS[platform];
  const count = variant.char_count;
  const overLimit = count > limit;
  const nearLimit = !overLimit && count >= Math.floor(limit * 0.9);

  return (
    <article className="rounded-xl border bg-white p-4">
      <header className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold capitalize text-slate-800">{platform} preview</h3>
        <span className={`text-xs ${overLimit ? "text-red-600" : nearLimit ? "text-amber-600" : "text-emerald-600"}`}>
          {count}/{limit}
        </span>
      </header>

      {imageUrl ? <img src={imageUrl} alt="Preview" className="mb-3 h-40 w-full rounded-lg object-cover" /> : null}

      <p className="whitespace-pre-wrap text-sm text-slate-800">{variant.text}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {hashtags.map((tag) => (
          <span key={tag} className="rounded-full bg-sky-50 px-2 py-1 text-xs text-sky-700">
            #{tag}
          </span>
        ))}
      </div>

      {ctaText ? (
        <div className="mt-4 rounded-lg bg-amber-50 p-2 text-xs text-amber-800">CTA: {ctaText}</div>
      ) : null}
    </article>
  );
};
