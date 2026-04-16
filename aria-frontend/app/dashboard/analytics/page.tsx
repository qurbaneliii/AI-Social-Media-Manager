"use client";

import { PlatformPieChart } from "@/components/dashboard/PlatformPieChart";
import { WeeklyChart } from "@/components/dashboard/WeeklyChart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboard } from "@/hooks/useDashboard";

export default function AnalyticsDashboardPage() {
  const { weeklyPerformance, platformBreakdown, statMetrics } = useDashboard();

  return (
    <div className="space-y-6">
      <div>
        <h1>Analytics Dashboard</h1>
        <p className="text-sm text-[var(--text-secondary)]">Track publishing velocity, engagement, and platform contribution.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statMetrics.slice(0, 4).map((item) => (
          <Card key={item.id}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-[var(--text-secondary)]">{item.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-black tabular-nums">{item.value}{item.valueSuffix ?? ""}</p>
              <p className="text-xs text-[var(--text-muted)]">{item.change > 0 ? "+" : ""}{item.change}% {item.changeLabel}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <WeeklyChart data={weeklyPerformance} />
        <PlatformPieChart data={platformBreakdown} />
      </div>
    </div>
  );
}
