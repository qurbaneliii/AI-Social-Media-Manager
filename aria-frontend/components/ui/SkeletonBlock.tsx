"use client";

import type { HTMLAttributes } from "react";

import { Skeleton } from "@/components/ui/skeleton";

type SkeletonBlockProps = HTMLAttributes<HTMLDivElement>;

export function SkeletonBlock({ className, ...props }: SkeletonBlockProps) {
  return <Skeleton className={className} {...props} />;
}
