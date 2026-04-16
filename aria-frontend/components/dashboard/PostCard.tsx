"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { CalendarClock, Ellipsis, Facebook, Heart, Instagram, Linkedin, MessageCircle, Repeat2, Twitter } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { DashboardPlatform, PostStatus } from "@/lib/mock-data";

interface PostCardProps {
  id: string;
  platform: DashboardPlatform;
  status: PostStatus;
  content: string;
  scheduledAt?: string;
  metrics: { likes: number; comments: number; shares: number };
}

const platformIconMap = {
  linkedin: Linkedin,
  twitter: Twitter,
  instagram: Instagram,
  facebook: Facebook
} as const;

const platformStyles: Record<DashboardPlatform, string> = {
  linkedin: "bg-[#0077B5]/15 text-[#0077B5]",
  twitter: "bg-slate-500/15 text-slate-700",
  instagram: "bg-pink-500/15 text-pink-600",
  facebook: "bg-[#1877F2]/15 text-[#1877F2]"
};

const statusVariants: Record<PostStatus, { label: string; variant: "warning" | "success" | "default" | "danger" }> = {
  scheduled: { label: "Scheduled", variant: "warning" },
  published: { label: "Published", variant: "success" },
  draft: { label: "Draft", variant: "default" },
  failed: { label: "Failed", variant: "danger" }
};

const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

const formatRelative = (iso: string): string => {
  const target = new Date(iso).getTime();
  const now = Date.now();
  const diffMs = target - now;
  const diffHours = Math.round(diffMs / 36e5);

  if (Math.abs(diffHours) < 24) {
    return `${rtf.format(diffHours, "hour")} at ${new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${rtf.format(diffDays, "day")} at ${new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

export function PostCard({ platform, status, content, scheduledAt, metrics }: PostCardProps) {
  const [expanded, setExpanded] = useState(false);

  const Icon = platformIconMap[platform];
  const statusMeta = statusVariants[status];

  const preview = useMemo(() => {
    if (expanded || content.length <= 132) {
      return content;
    }
    return `${content.slice(0, 132)}...`;
  }, [content, expanded]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="h-full min-w-[290px] max-w-[360px]"
    >
      <Card className="h-full border-transparent transition-all duration-200 hover:border-[var(--brand-primary)]">
        <CardContent className="flex h-full flex-col gap-4 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={cn("grid h-9 w-9 place-items-center rounded-xl", platformStyles[platform])}>
                <Icon className="h-4 w-4" />
              </span>
              <Badge variant={statusMeta.variant}>{statusMeta.label}</Badge>
            </div>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <Ellipsis className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-44">
                <DropdownMenuItem>Edit</DropdownMenuItem>
                <DropdownMenuItem>Duplicate</DropdownMenuItem>
                <DropdownMenuItem>View Analytics</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-red-600">Delete</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <button
            type="button"
            className="text-left text-sm leading-6 text-[var(--text-secondary)]"
            onClick={() => setExpanded((prev) => !prev)}
          >
            {preview}
          </button>

          <div className="mt-auto space-y-2">
            {scheduledAt ? (
              <p className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
                <CalendarClock className="h-3.5 w-3.5" />
                {formatRelative(scheduledAt)}
              </p>
            ) : null}

            <div className="flex items-center gap-3 text-xs text-[var(--text-secondary)]">
              <span className="inline-flex items-center gap-1">
                <Heart className="h-3.5 w-3.5" />
                {metrics.likes}
              </span>
              <span className="inline-flex items-center gap-1">
                <MessageCircle className="h-3.5 w-3.5" />
                {metrics.comments}
              </span>
              <span className="inline-flex items-center gap-1">
                <Repeat2 className="h-3.5 w-3.5" />
                {metrics.shares}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
