"use client";

import { CalendarClock } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboard } from "@/hooks/useDashboard";

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function SchedulerPage() {
  const { posts } = useDashboard();

  const scheduledPosts = posts.filter((post) => post.status === "scheduled");

  return (
    <div className="space-y-6">
      <div>
        <h1>Scheduler</h1>
        <p className="text-sm text-[var(--text-secondary)]">Plan upcoming content in a calendar-focused workflow.</p>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Weekly Calendar</CardTitle>
          <p className="inline-flex items-center gap-1 text-xs text-[var(--text-muted)]">
            <CalendarClock className="h-3.5 w-3.5" />
            Week of Apr 14
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-7">
            {days.map((day, idx) => (
              <div key={day} className="min-h-[140px] rounded-xl border border-[var(--border)] bg-[var(--bg-surface)] p-3">
                <p className="text-xs font-semibold text-[var(--text-secondary)]">{day}</p>
                <div className="mt-2 space-y-2">
                  {scheduledPosts[idx] ? (
                    <div className="rounded-md bg-[var(--bg-elevated)] p-2 text-xs text-[var(--text-secondary)]">{scheduledPosts[idx].content.slice(0, 80)}...</div>
                  ) : (
                    <div className="rounded-md border border-dashed border-[var(--border)] p-2 text-xs text-[var(--text-muted)]">No post</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
