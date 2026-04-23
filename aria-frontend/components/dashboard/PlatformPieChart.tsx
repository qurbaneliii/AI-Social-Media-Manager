"use client";

import { useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Sector, Tooltip } from "recharts";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PlatformBreakdown } from "@/lib/mock-data";
import { platformLabels } from "@/lib/mock-data";

interface PlatformPieChartProps {
  data: PlatformBreakdown[];
}

export function PlatformPieChart({ data }: PlatformPieChartProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  const dominant = useMemo(() => {
    if (!data.length) {
      return null;
    }
    return [...data].sort((a, b) => b.value - a.value)[0];
  }, [data]);

  const renderActiveShape = (props: unknown) => {
    const sector = props as {
      cx?: number;
      cy?: number;
      innerRadius?: number;
      outerRadius?: number;
      startAngle?: number;
      endAngle?: number;
      fill?: string;
    } | null;
    if (!sector) {
      return <g />;
    }

    return (
      <Sector
        cx={sector.cx ?? 0}
        cy={sector.cy ?? 0}
        innerRadius={sector.innerRadius ?? 0}
        outerRadius={(sector.outerRadius ?? 0) + 8}
        startAngle={sector.startAngle ?? 0}
        endAngle={sector.endAngle ?? 0}
        fill={sector.fill ?? "#94a3b8"}
      />
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Platform Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-[1fr_190px]">
          <div className="h-[280px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="platform"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  activeIndex={activeIndex}
                  onMouseEnter={(_, index: number) => setActiveIndex(index)}
                  activeShape={renderActiveShape}
                  animationBegin={0}
                  animationDuration={1200}
                >
                  {data.map((entry) => (
                    <Cell key={entry.platform} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) {
                      return null;
                    }
                    const item = payload[0].payload as PlatformBreakdown;
                    return (
                      <div
                        style={{
                          borderRadius: 10,
                          border: "1px solid var(--border)",
                          background: "var(--bg-surface)",
                          padding: "8px 10px",
                          fontSize: 12
                        }}
                      >
                        <p style={{ fontWeight: 600 }}>{platformLabels[item.platform]}</p>
                        <p>{item.count} posts</p>
                        <p>{item.value}% share</p>
                      </div>
                    );
                  }}
                />
                {dominant ? (
                  <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle">
                    <tspan x="50%" dy="-0.3em" className="fill-[var(--text-secondary)] text-xs">
                      {platformLabels[dominant.platform]}
                    </tspan>
                    <tspan x="50%" dy="1.4em" className="fill-[var(--text-primary)] text-base font-bold">
                      {dominant.value}%
                    </tspan>
                  </text>
                ) : null}
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-3">
            {data.map((item) => (
              <div key={item.platform} className="flex items-center justify-between rounded-lg border border-[var(--border)] px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-[var(--text-secondary)]">{platformLabels[item.platform]}</span>
                </div>
                <span className="text-sm font-semibold">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
