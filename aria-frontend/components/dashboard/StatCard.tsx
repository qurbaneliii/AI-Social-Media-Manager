"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { Line, LineChart, ResponsiveContainer } from "recharts";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { useCountUp } from "@/hooks/useCountUp";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  change: number;
  changeLabel: string;
  icon: LucideIcon;
  iconColor: string;
  trend?: number[];
  valuePrefix?: string;
  valueSuffix?: string;
  index?: number;
}

const formatNumber = (value: number): string => {
  if (Number.isInteger(value)) {
    return new Intl.NumberFormat("en-US").format(value);
  }
  return value.toFixed(1);
};

export function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  iconColor,
  trend,
  valuePrefix,
  valueSuffix,
  index = 0
}: StatCardProps) {
  const animatedValue = useCountUp(typeof value === "number" ? value : 0, {
    decimals: typeof value === "number" && Number.isInteger(value) ? 0 : 1
  });

  const displayValue = typeof value === "number" ? formatNumber(animatedValue) : value;
  const changeVariant = change > 0 ? "success" : change < 0 ? "danger" : "default";
  const symbol = change > 0 ? "↑" : change < 0 ? "↓" : "→";

  const trendData = (trend ?? []).map((item, pointIndex) => ({
    pointIndex,
    value: item
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1, ease: "easeOut" }}
      whileHover={{ y: -2 }}
      className="h-full"
    >
      <Card className="h-full transition-all duration-200 hover:shadow-md">
        <CardContent className="space-y-4 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <p className="label-xs">{title}</p>
              <p className="stat-value leading-none">
                {valuePrefix}
                {displayValue}
                {valueSuffix}
              </p>
            </div>
            <div className={cn("grid h-10 w-10 place-items-center rounded-xl", iconColor)}>
              <Icon className="h-5 w-5" />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant={changeVariant} className="rounded-md px-2 py-1 font-semibold">
              {symbol} {Math.abs(change).toFixed(1)}%
            </Badge>
            <p className="text-xs text-[var(--text-secondary)]">{changeLabel}</p>
          </div>

          {trendData.length > 0 ? (
            <div className="h-10 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="var(--brand-primary)"
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive
                    animationDuration={900}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}
