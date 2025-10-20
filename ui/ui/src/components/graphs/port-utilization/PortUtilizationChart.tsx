/*
 * File: PortUtilizationChart.tsx
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
import { AggregateTimeSeriesPoint } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";
import { CHART_COLORS, STATUS_COLORS, getChartColor } from "@/lib/chartColors";

interface PortUtilizationChartProps {
  data: AggregateTimeSeriesPoint[];
  selectedPorts: string[];
}

export function PortUtilizationChart({
  data,
  selectedPorts,
}: PortUtilizationChartProps) {
  const { getT } = useLanguage();

  // Group data by port (ip_address - port_name)
  const portGroups = new Map<string, AggregateTimeSeriesPoint[]>();

  data.forEach((point) => {
    const portKey = `${point.ip_address} - ${point.port_name}`;
    if (!portGroups.has(portKey)) {
      portGroups.set(portKey, []);
    }
    portGroups.get(portKey)!.push(point);
  });

  // Get unique port keys
  const allPortKeys = Array.from(portGroups.keys());

  // Filter ports if specific ports are selected
  const displayPortKeys =
    selectedPorts.length === 0
      ? allPortKeys
      : allPortKeys.filter((key) => selectedPorts.includes(key));

  // Transform data for recharts
  // Group by timestamp, then add all ports as columns
  const timeMap = new Map<string, Record<string, string | number>>();

  data.forEach((point) => {
    const portKey = `${point.ip_address} - ${point.port_name}`;

    // Skip if this port is filtered out
    if (displayPortKeys.length > 0 && !displayPortKeys.includes(portKey)) {
      return;
    }

    const time = point.bucket_time;

    if (!timeMap.has(time)) {
      timeMap.set(time, { time });
    }

    const dataPoint = timeMap.get(time)!;
    // Convert to percentage and cap at 100% to handle API edge cases
    dataPoint[`${portKey}_utilization`] = Math.min(
      point.avg_utilization * 100,
      100
    );
    dataPoint[`${portKey}_throughput`] = point.avg_throughput;
    dataPoint[`${portKey}_max_utilization`] = Math.min(
      point.max_utilization * 100,
      100
    );
  });

  const chartData = Array.from(timeMap.values()).sort(
    (a, b) =>
      new Date(a.time as string).getTime() -
      new Date(b.time as string).getTime()
  );

  // Build chart config
  const chartConfig: ChartConfig = {};
  displayPortKeys.forEach((portKey, index) => {
    chartConfig[`${portKey}_utilization`] = {
      label: portKey,
      color: getChartColor(index),
    };
  });

  // Format time for display
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Custom tooltip content
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const timeValue = payload[0]?.payload?.time;

    return (
      <div className="bg-background border border-border rounded-md shadow-md p-3">
        <p className="text-sm font-medium mb-2">
          {timeValue ? formatTime(timeValue) : ""}
        </p>
        <div className="space-y-1">
          {displayPortKeys.map((portKey, index) => {
            const utilization = payload[0]?.payload[`${portKey}_utilization`];
            const throughput = payload[0]?.payload[`${portKey}_throughput`];
            const maxUtilization =
              payload[0]?.payload[`${portKey}_max_utilization`];

            if (utilization === undefined) return null;

            // Ensure values are numbers, cap at 100%, and handle edge cases
            const utilValue =
              typeof utilization === "number" ? Math.min(utilization, 100) : 0;
            const maxUtilValue =
              typeof maxUtilization === "number"
                ? Math.min(maxUtilization, 100)
                : 0;
            const throughputValue =
              typeof throughput === "number" ? throughput : 0;

            return (
              <div key={portKey} className="text-xs">
                <div
                  className="font-medium"
                  style={{
                    color: getChartColor(index),
                  }}
                >
                  {portKey}
                </div>
                <div className="text-muted-foreground ml-2">
                  {getT("page.PortUtilizationPage.utilization", "Utilization")}:{" "}
                  {utilValue.toFixed(2)}%
                  {maxUtilValue !== undefined && maxUtilValue >= utilValue && (
                    <span
                      className="ml-1 font-medium"
                      style={{ color: STATUS_COLORS.warning }}
                    >
                      (peak: {maxUtilValue.toFixed(2)}%)
                    </span>
                  )}
                </div>
                <div className="text-muted-foreground ml-2">
                  {getT("page.PortUtilizationPage.throughput", "Throughput")}:{" "}
                  {throughputValue.toFixed(2)} Mbps
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
          dataKey="time"
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
            value: getT(
              "page.PortUtilizationPage.utilization",
              "Utilization (%)"
            ),
            angle: -90,
            position: "insideLeft",
          }}
        />
        <ChartTooltip content={<CustomTooltip />} />
        <ChartLegend content={<ChartLegendContent />} />
        {displayPortKeys.map((portKey, index) => (
          <Line
            key={portKey}
            type="monotone"
            dataKey={`${portKey}_utilization`}
            stroke={getChartColor(index)}
            strokeWidth={3}
            dot={false}
            name={portKey}
            connectNulls
            isAnimationActive={false}
          />
        ))}
      </LineChart>
    </ChartContainer>
  );
}
