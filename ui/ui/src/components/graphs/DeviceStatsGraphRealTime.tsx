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
import { useLanguage } from "@/context/languageContext";
import { DeviceStatsMessage, WebSocketMessage } from "@/lib/types";

const chartConfig = {
  cpu: {
    label: "CPU",
    color: "var(--stats-chart-1)",
  },
  memory: {
    label: "Memory",
    color: "var(--stats-chart-2)",
  },
  disk: {
    label: "Disk",
    color: "var(--stats-chart-3)",
  },
};

function formatTime(value: number) {
  const d = new Date(value);
  return d.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function DeviceStatsGraphRealTime({
  switchId,
  ipAddress,
}: {
  switchId: string;
  ipAddress: string;
}) {
  const { getT } = useLanguage();
  const { subscribe } = useMultiWebSocket();
  const [data, setData] = useState<
    Array<{
      ts: number;
      cpu: number | null;
      memory: number | null;
      disk: number | null;
    }>
  >([]);
  // Keep a sliding window of the last 5 minutes of points
  const WINDOW_MS = 5 * 60 * 1000;

  // Store all received points (for 5 min window)
  const allPoints = useRef<
    Array<{
      ts: number;
      cpu: number | null;
      memory: number | null;
      disk: number | null;
    }>
  >([]);

  useEffect(() => {
    const unsubscribe = subscribe("deviceStats", (msg: WebSocketMessage) => {
      if (
        msg.type === "stats" &&
        (msg as DeviceStatsMessage).data?.ip_address === ipAddress
      ) {
        const now = Date.now();
        const cutoff = now - WINDOW_MS;
        const newPoint = {
          ts: now,
          cpu: (msg as DeviceStatsMessage).data.cpu,
          memory: (msg as DeviceStatsMessage).data.memory,
          disk: (msg as DeviceStatsMessage).data.disk,
        };
        // Append and trim in-place to maintain a stable, bounded buffer
        const points = allPoints.current;
        points.push(newPoint);
        // Remove all points older than the sliding window
        while (points.length > 0 && points[0].ts < cutoff) {
          points.shift();
        }
        setData([...points]);
      }
    });
    return unsubscribe;
  }, [subscribe, ipAddress]);

  const chartData = [...data];
  const now = Date.now();
  const minTime = now - WINDOW_MS;
  const maxTime = now;

  return (
    <div className="w-full flex justify-center pt-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{getT("components.graphs.device_stats.title")}</CardTitle>
          <CardDescription>
            {getT("components.graphs.device_stats.description")}
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
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={32}
                tickFormatter={formatTime}
                domain={[minTime, maxTime]}
                type="number"
                scale="time"
              />
              <YAxis domain={[0, 100]} />
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
              <Area
                strokeWidth={2}
                type="monotone"
                dataKey="cpu"
                stroke="var(--stats-chart-1)"
                fill="var(--stats-chart-1)"
                fillOpacity={0.2}
                animationEasing="linear"
                animationDuration={0}
              />
              <Area
                strokeWidth={2}
                type="monotone"
                dataKey="memory"
                stroke="var(--stats-chart-2)"
                fill="var(--stats-chart-2)"
                fillOpacity={0.2}
                animationEasing="linear"
                animationDuration={0}
              />
              <Area
                strokeWidth={2}
                type="monotone"
                dataKey="disk"
                stroke="var(--stats-chart-3)"
                fill="var(--stats-chart-3)"
                fillOpacity={0.2}
                animationEasing="linear"
                animationDuration={0}
              />
              <ChartLegend content={<ChartLegendContent />} />
            </AreaChart>
          </ChartContainer>
        </CardContent>
        <CardFooter>
          <div className="flex w-full items-start gap-2 text-sm">
            <div className="grid gap-2">
              <div className="flex items-center gap-2 leading-none font-medium">
                {getT("components.graphs.device_stats.live_stats")}{" "}
                <span className="font-mono">{switchId}</span>
                <TrendingUp className="h-4 w-4" />
              </div>
              <div className="text-muted-foreground flex items-center gap-2 leading-none">
                {getT("components.graphs.device_stats.last_5_minutes")}
              </div>
            </div>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
