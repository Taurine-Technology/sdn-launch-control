/**
 * File: PortStatsGraph.tsx
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
import { useEffect, useRef, useState } from "react";
import { useMultiWebSocket } from "@/context/MultiWebSocketContext";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import { Port } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

interface PortStatsGraphProps {
  targetIpAddress: string;
  targetPorts: Port[];
}

interface PortDataPoint {
  ts: number;
  [key: string]: string | number | null;
}

interface OpenFlowMessage {
  message?: {
    ip_address?: string;
    ports?: Record<string, number>;
  };
}

// Dynamic chart config will be created based on port names
const createChartConfig = (ports: Port[]) => {
  const config: Record<string, { label: string; color: string }> = {};
  const portColors = [
    "var(--port-stats-chart-1)",
    "var(--port-stats-chart-2)",
    "var(--port-stats-chart-3)",
    "var(--port-stats-chart-4)",
    "var(--port-stats-chart-5)",
  ];

  ports.forEach((port, index) => {
    const colorIndex = index % portColors.length;
    // Create config for both the port name and port number (if it exists)
    config[port.name] = {
      label: `Port ${port.name}`,
      color: portColors[colorIndex],
    };

    // If port has a number, also create config for the number key
    if (port.ovs_port_number) {
      config[port.ovs_port_number.toString()] = {
        label: `Port ${port.name}`,
        color: portColors[colorIndex],
      };
    }
  });
  return config;
};

function formatTime(value: number) {
  const d = new Date(value);
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

const WINDOW_MS = 5 * 60 * 1000;

export default function PortStatsGraph({
  targetIpAddress,
  targetPorts,
}: PortStatsGraphProps) {
  const { getT } = useLanguage();
  const { subscribe } = useMultiWebSocket();
  const [data, setData] = useState<PortDataPoint[]>([]);
  // Store all received points (for 5 minute window)
  const allPoints = useRef<PortDataPoint[]>([]);
  // Track which data keys are actually used for each port
  const [portDataKeyMap, setPortDataKeyMap] = useState<Record<string, string>>(
    {}
  );

  // Create dynamic chart config based on target ports
  const chartConfig = createChartConfig(targetPorts);

  // When the target ports set changes, reset the mapping to avoid stale keys
  useEffect(() => {
    setPortDataKeyMap({});
  }, [targetPorts]);

  useEffect(() => {
    const unsubscribe = subscribe("openflow", (msg) => {
      const openFlowMsg = msg as OpenFlowMessage;
      if (
        openFlowMsg.message?.ip_address === targetIpAddress &&
        openFlowMsg.message.ports
      ) {
        const portsData = openFlowMsg.message.ports;

        let targetPortNames = targetPorts.map((p) => p.name);

        // Filter ports based on target port names
        let filteredPorts: Record<string, number> = {};
        const newPortDataKeyMap: Record<string, string> = {};

        // First try exact match
        filteredPorts = Object.keys(portsData)
          .filter((key) => targetPortNames.includes(key))
          .reduce((obj, key) => {
            obj[key] = portsData[key];
            // Track that this port uses its name as the data key
            const portObj = targetPorts.find((p) => p.name === key);
            if (portObj) {
              newPortDataKeyMap[portObj.name] = key;
            }
            return obj;
          }, {} as Record<string, number>);

        if (
          Object.keys(filteredPorts).length === 0 &&
          Object.keys(portsData).length > 0
        ) {
          targetPortNames = targetPorts.map(
            (p) => p.ovs_port_number?.toString() || ""
          );
          const integerPortNames = targetPortNames.map((name) => {
            if (!isNaN(Number(name))) {
              return name;
            }
            return null;
          });

          if (integerPortNames.length > 0) {
            filteredPorts = Object.keys(portsData)
              .filter((key) => integerPortNames.includes(key))
              .reduce((obj, key) => {
                obj[key] = portsData[key];
                // Track that this port uses its number as the data key
                const portObj = targetPorts.find(
                  (p) => p.ovs_port_number?.toString() === key
                );
                if (portObj) {
                  newPortDataKeyMap[portObj.name] = key;
                }
                return obj;
              }, {} as Record<string, number>);
          }
        }

        // If no exact matches, try fallback matching (remove 'eth' prefix)
        else if (
          Object.keys(filteredPorts).length === 0 &&
          Object.keys(portsData).length > 0
        ) {
          const modifiedNameToOriginalMap: Record<string, string> = {};
          const modifiedTargetPortNames = targetPortNames.map((name) => {
            const modifiedName = name.startsWith("eth")
              ? name.substring(3)
              : name;
            modifiedNameToOriginalMap[modifiedName] = name;
            return modifiedName;
          });

          Object.keys(portsData).forEach((wsKey) => {
            if (modifiedTargetPortNames.includes(wsKey)) {
              const originalTargetName = modifiedNameToOriginalMap[wsKey];
              filteredPorts[originalTargetName] = portsData[wsKey];
              // Track that this port uses the original name as the data key
              newPortDataKeyMap[originalTargetName] = originalTargetName;
            }
          });
        }

        if (Object.keys(filteredPorts).length > 0) {
          // Update the port data key mapping
          setPortDataKeyMap((prev) => ({ ...prev, ...newPortDataKeyMap }));

          const now = Date.now();
          const cutoff = now - WINDOW_MS;
          const newPoint: PortDataPoint = {
            ts: now,
            ...filteredPorts,
          };

          // Append and trim in-place to maintain a stable, bounded buffer
          const points = allPoints.current;
          points.push(newPoint);
          // Remove all points older than the sliding window
          const firstValidIndex = points.findIndex((p) => p.ts >= cutoff);
          if (firstValidIndex > 0) {
            points.splice(0, firstValidIndex);
          } else if (firstValidIndex === -1 && points.length > 1) {
            // All points except the last are old
            points.splice(0, points.length - 1);
          }
          setData([...points]);
        }
      }
    });
    return unsubscribe;
  }, [subscribe, targetIpAddress, targetPorts]);

  const chartData = data;
  const now = Date.now();
  const minTime = now - WINDOW_MS;
  const maxTime = now;

  return (
    <div className="w-full flex justify-center pt-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{getT("components.graphs.port_stats.title")}</CardTitle>
          <CardDescription>
            {getT("components.graphs.port_stats.description")}
          </CardDescription>
        </CardHeader>
        <CardContent className="lg:max-h-[220px] 2xl:max-h-[420px]">
          <ChartContainer config={chartConfig} className="w-full h-full">
            <AreaChart
              accessibilityLayer
              data={chartData}
              margin={{ left: 12, right: 12 }}
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="ts"
                type="number"
                scale="time"
                domain={[minTime, maxTime]}
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={32}
                tickFormatter={formatTime}
              />
              <YAxis
                domain={["auto", "auto"]}
                label={{
                  value: "Throughput (Mbps)",
                  angle: -90,
                  position: "insideLeft",
                }}
              />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    indicator="line"
                    labelFormatter={(_value, payload) => {
                      const ts = Number(payload?.[0]?.payload?.ts);
                      return Number.isFinite(ts) ? formatTime(ts) : "";
                    }}
                  />
                }
              />
              {targetPorts.map((portObj) => {
                const portName = portObj.name;

                // Use the tracked data key for this port, or fallback to port name
                const dataKey = portDataKeyMap[portName] || portName;

                // Get the config for the actual data key being used
                const config = chartConfig[dataKey] || chartConfig[portName];

                return (
                  <Area
                    key={portName}
                    strokeWidth={2}
                    type="monotone"
                    dataKey={dataKey}
                    stroke={config.color}
                    fill={config.color}
                    fillOpacity={0.2}
                    animationEasing="linear"
                    animationDuration={0}
                    name={config.label}
                  />
                );
              })}
              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        </CardContent>
        <CardFooter>
          <div className="flex w-full items-start gap-2 text-sm">
            <div className="grid gap-2">
              <div className="flex items-center gap-2 leading-none font-medium">
                {getT("components.graphs.port_stats.live_port_stats")}{" "}
                <span className="font-mono">{targetIpAddress}</span>
                <TrendingUp className="h-4 w-4" />
              </div>
              <div className="text-muted-foreground flex items-center gap-2 leading-none">
                {getT("components.graphs.port_stats.last_5_minutes")}
              </div>
            </div>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
