"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { WeeklyMetric } from "@/lib/mock-data";

interface WeeklyChartProps {
  data: WeeklyMetric[];
}

interface TooltipPayloadItem {
  color?: string;
  name?: string;
  value?: number;
}

function WeeklyTooltip({ active, payload, label }: { active?: boolean; payload?: TooltipPayloadItem[]; label?: string }) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 shadow-xl">
      <p className="mb-1 font-semibold">{label}</p>
      {payload.map((item) => (
        <p key={item.name} className="flex items-center gap-2 text-slate-200">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: item.color }} />
          <span>{item.name}:</span>
          <span className="font-medium">{item.value}</span>
        </p>
      ))}
    </div>
  );
}

export function WeeklyChart({ data }: WeeklyChartProps) {
  if (!data.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Weekly Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid h-[280px] place-items-center rounded-xl border border-dashed border-[var(--border)] text-sm text-[var(--text-secondary)]">
            No performance data available yet.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Weekly Performance</CardTitle>
          <p className="text-xs text-[var(--text-secondary)]">Mon - Sun</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">Apr 10 - Apr 16</Badge>
          <div className="hidden items-center gap-1 sm:flex">
            <Badge className="bg-teal-500/15 text-teal-700">Posts</Badge>
            <Badge className="bg-blue-500/15 text-blue-700">Engagement</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="postsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#14B8A6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="engagementGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0077B5" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#0077B5" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="color-mix(in srgb, var(--border) 85%, transparent)" />
              <XAxis dataKey="day" axisLine={false} tickLine={false} />
              <YAxis yAxisId="left" axisLine={false} tickLine={false} width={32} />
              <YAxis yAxisId="right" orientation="right" axisLine={false} tickLine={false} width={36} />
              <Tooltip content={<WeeklyTooltip />} />
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="posts"
                stroke="#14B8A6"
                fill="url(#postsGradient)"
                strokeWidth={2.2}
                animationDuration={1500}
              />
              <Area
                yAxisId="right"
                type="monotone"
                dataKey="engagement"
                stroke="#0077B5"
                fill="url(#engagementGradient)"
                strokeWidth={2.2}
                animationDuration={1500}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
