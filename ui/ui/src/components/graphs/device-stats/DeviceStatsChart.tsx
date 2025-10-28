/**
 * File: DeviceStatsChart.tsx
 * Copyright (C) 2025 Keegan White
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Keegan White exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

"use client";

import { Line, LineChart, CartesianGrid, XAxis, YAxis } from "recharts";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartLegend,
  ChartLegendContent,
} from "@/components/ui/chart";
import { DeviceStatsTimeSeriesPoint } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";
import { getChartColor } from "@/lib/chartColors";

interface Props {
  data: DeviceStatsTimeSeriesPoint[];
}

export function DeviceStatsChart({ data }: Props) {
  const { getT } = useLanguage();

  // Transform data for recharts (already bucketed and ordered by backend)
  const chartData = data.map((p) => ({
    time: p.bucket_time,
    ts: new Date(p.bucket_time).getTime(),
    cpu: p.cpu_avg ?? null,
    memory: p.memory_avg ?? null,
    disk: p.disk_avg ?? null,
    cpu_max: p.cpu_max ?? null,
    memory_max: p.memory_max ?? null,
    disk_max: p.disk_max ?? null,
  }));

  const chartConfig: ChartConfig = {
    cpu: { label: "CPU", color: getChartColor(0) },
    memory: { label: "Memory", color: getChartColor(1) },
    disk: { label: "Disk", color: getChartColor(2) },
  };

  const formatTime = (value: number) => {
    const d = new Date(value);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  // Custom tooltip content
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{
      payload: Record<string, string | number | null>;
    }>;
  }) => {
    if (!active || !payload || payload.length === 0) return null;

    const timeValue = payload[0]?.payload?.ts;

    return (
      <div className="bg-background border border-border rounded-md shadow-md p-3">
        <p className="text-sm font-medium mb-2">
          {timeValue ? formatTime(Number(timeValue)) : ""}
        </p>
        <div className="space-y-1">
          {["cpu", "memory", "disk"].map((metric, index) => {
            const value = payload[0]?.payload[metric];
            const maxValue = payload[0]?.payload[`${metric}_max`];

            if (value === undefined) return null;

            const metricValue = typeof value === "number" ? value : null;
            const maxMetricValue =
              typeof maxValue === "number" ? maxValue : null;

            return (
              <div key={metric} className="text-xs">
                <div
                  className="font-medium"
                  style={{
                    color: getChartColor(index),
                  }}
                >
                  {metric.charAt(0).toUpperCase() + metric.slice(1)}
                </div>
                <div className="text-muted-foreground ml-2">
                  {getT(
                    `page.DeviceStatsPage.${metric}`,
                    metric.charAt(0).toUpperCase() + metric.slice(1)
                  )}
                  : {metricValue === null ? "—" : `${metricValue.toFixed(2)}%`}
                  {maxMetricValue !== null &&
                    (metricValue === null || maxMetricValue >= metricValue) && (
                      <span
                        className="ml-1 font-medium"
                        style={{ color: getChartColor(index) }}
                      >
                        (peak: {maxMetricValue.toFixed(2)}%)
                      </span>
                    )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <ChartContainer config={chartConfig} className="h-[400px] w-full">
      <LineChart
        data={chartData}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="ts"
          type="number"
          scale="time"
          domain={["dataMin", "dataMax"]}
          tickFormatter={formatTime}
          tickLine={false}
          axisLine={false}
          tickMargin={8}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          domain={[0, 100]}
          label={{
            value: getT("page.DeviceStatsPage.percentage", "Percentage (%)"),
            angle: -90,
            position: "insideLeft",
          }}
        />
        <ChartTooltip content={<CustomTooltip />} />
        <ChartLegend content={<ChartLegendContent />} />
        <Line
          type="monotone"
          dataKey="cpu"
          stroke={getChartColor(0)}
          strokeWidth={3}
          dot={false}
          name="CPU"
          // connectNulls={false} // default
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="memory"
          stroke={getChartColor(1)}
          strokeWidth={3}
          dot={false}
          name="Memory"
          // connectNulls={false}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="disk"
          stroke={getChartColor(2)}
          strokeWidth={3}
          dot={false}
          name="Disk"
          // connectNulls={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
