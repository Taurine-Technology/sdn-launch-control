"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, XAxis, YAxis, LabelList } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip } from "@/components/ui/chart";
import { useAuth } from "@/context/authContext";
import { fetchAggregateFlowsByUser } from "@/lib/networkData";

interface UserActivityData {
  name: string;
  value: number;
}

type TimeRange = "5min" | "1hour" | "24hour" | "7days";

interface UserActivityChartProps {
  timeRange: TimeRange;
}

export default function UserActivityChart({
  timeRange,
}: UserActivityChartProps) {
  const { token } = useAuth();
  const [data, setData] = useState<UserActivityData[]>([]);

  // Convert time range to period string for API
  const getPeriodString = (range: TimeRange): string => {
    switch (range) {
      case "5min":
        return "5 minutes";
      case "1hour":
        return "1 hour";
      case "24hour":
        return "24 hours";
      case "7days":
        return "7 days";
      default:
        return "1 hour";
    }
  };

  // Format bytes to human-readable format (KB, MB, GB, TB)
  const formatBytes = (mb: number): string => {
    // Convert MB to bytes first
    const bytes = mb * 1024 * 1024;
    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  // Get the appropriate unit for the Y-axis based on data range
  const getYAxisUnit = (): { unit: string; formatter: (val: number) => string } => {
    if (data.length === 0) {
      return { unit: "MB", formatter: (v) => `${v.toFixed(0)}` };
    }

    // Find max value in data
    const maxValue = Math.max(...data.map((d) => d.value));

    // Convert MB to bytes to determine appropriate unit
    const maxBytes = maxValue * 1024 * 1024;

    if (maxBytes >= 1024 * 1024 * 1024 * 1024) {
      // TB
      return {
        unit: "TB",
        formatter: (v) => `${(v / (1024 * 1024)).toFixed(1)}`,
      };
    } else if (maxBytes >= 1024 * 1024 * 1024) {
      // GB
      return {
        unit: "GB",
        formatter: (v) => `${(v / 1024).toFixed(1)}`,
      };
    } else if (maxBytes >= 1024 * 1024) {
      // MB (current)
      return {
        unit: "MB",
        formatter: (v) => `${v.toFixed(0)}`,
      };
    } else if (maxBytes >= 1024) {
      // KB
      return {
        unit: "KB",
        formatter: (v) => `${(v * 1024).toFixed(0)}`,
      };
    }
    // Bytes
    return {
      unit: "B",
      formatter: (v) => `${(v * 1024 * 1024).toFixed(0)}`,
    };
  };

  const yAxisConfig = getYAxisUnit();

  useEffect(() => {
    if (!token) return;
    const load = async () => {
      const period = getPeriodString(timeRange);
      const res = await fetchAggregateFlowsByUser(token, period);
      // Transform { mac: bytes } -> [{ name: mac, value: mb }]
      const sorted = Object.entries(res)
        .map(([mac, bytes]) => ({
          name: mac,
          value: Number((bytes / 1024 / 1024).toFixed(2)), // MB
        }))
        .sort((a, b) => b.value - a.value);
        // .slice(0, 5); // Removed slice to show all users
      setData(sorted);
    };
    load();
    // Refresh interval based on time range
    const refreshInterval =
      timeRange === "5min"
        ? 30000 // 30 seconds
        : timeRange === "1hour"
        ? 60000 // 1 minute
        : timeRange === "24hour"
        ? 300000 // 5 minutes
        : 600000; // 10 minutes for 7 days
    const interval = setInterval(load, refreshInterval);
    return () => clearInterval(interval);
  }, [token, timeRange]);

  // Get top user (first in sorted array)
  const topUser = data.length > 0 ? data[0] : null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>User Data Consumption</CardTitle>
        {topUser && (
          <div className="mt-4 space-y-1">
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-semibold">Top User:</span>
              <span className="text-base font-bold">{topUser.name}</span>
            </div>
            <div className="text-sm text-muted-foreground">
              {formatBytes(topUser.value)} Consumed
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No user activity data available for the selected time range.
            </div>
        ) : (
        <ChartContainer
          config={{ value: { label: yAxisConfig.unit, color: "#a855f7" } }}
          className="h-[300px] w-full"
        >
          <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
            <XAxis 
              type="number" 
              hide
              tickFormatter={yAxisConfig.formatter}
            />
            <YAxis
              dataKey="name"
              type="category"
              width={120}
              tick={{ fontSize: 12 }}
            />
            <ChartTooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const data = payload[0];
                const value = data.value as number;
                const name = data.payload?.name as string;
                return (
                  <div className="rounded-lg border bg-background p-2 shadow-sm">
                    <p className="text-sm font-medium mb-2">{name || "Unknown"}</p>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="font-medium">Data:</span>
                      <span className="font-mono">
                        {formatBytes(value)}
                      </span>
                    </div>
                  </div>
                );
              }}
            />
            <Bar dataKey="value" fill="#a855f7" radius={4}>
              <LabelList
                dataKey="value"
                position="right"
                formatter={(v: number) => formatBytes(v)}
              />
            </Bar>
          </BarChart>
        </ChartContainer>
        )}
      </CardContent>
    </Card>
  );
}

