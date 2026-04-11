// filename: lib/utils.ts
// purpose: Shared utility helpers for classnames and formatting.
// dependencies: clsx, tailwind-merge

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export const cn = (...inputs: ClassValue[]): string => twMerge(clsx(inputs));

export const secondsToMmSs = (total: number): string => {
  const mins = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const secs = Math.floor(total % 60)
    .toString()
    .padStart(2, "0");
  return `${mins}:${secs}`;
};

export const titleCase = (value: string): string =>
  value
    .split(/[\s_-]+/)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1).toLowerCase())
    .join(" ");
