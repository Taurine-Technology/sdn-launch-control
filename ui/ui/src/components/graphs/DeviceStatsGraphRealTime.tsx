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

function formatTime(iso: string) {
  const d = new Date(iso);
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
      time: string;
      cpu: number | null;
      memory: number | null;
      disk: number | null;
    }>
  >([]);
  const startTimeRef = useRef(Date.now());
  // Add a 1-second buffer to the left (start) of the x-axis
  const [minTime, setMinTime] = useState<string>(
    new Date(startTimeRef.current - 1000).toISOString()
  );
  const [maxTime, setMaxTime] = useState<string>(
    new Date(Date.now()).toISOString()
  );

  // Store all received points (for 5 min window)
  const allPoints = useRef<
    Array<{
      time: string;
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
        const newPoint = {
          time: new Date().toISOString(),
          cpu: (msg as DeviceStatsMessage).data.cpu,
          memory: (msg as DeviceStatsMessage).data.memory,
          disk: (msg as DeviceStatsMessage).data.disk,
        };
        allPoints.current = [...allPoints.current, newPoint].filter(
          (d) => new Date(d.time).getTime() >= startTimeRef.current - 1000
        );
        // minTime: 1 second before the time we joined (fixed)
        setMinTime(new Date(startTimeRef.current - 1000).toISOString());
        // maxTime: latest data point or now
        setMaxTime(
          new Date(
            Math.max(now, new Date(newPoint.time).getTime())
          ).toISOString()
        );
        setData([...allPoints.current]);
      }
    });
    return unsubscribe;
  }, [subscribe, ipAddress]);

  // Keep the x-axis buffer on the left fixed, and update the right as new data arrives
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setMinTime(new Date(startTimeRef.current - 1000).toISOString());
      setMaxTime(new Date(now).toISOString());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const chartData = [...data];

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
                dataKey="time"
                tickLine={false}
                axisLine={false}
                tickMargin={8}
                minTickGap={32}
                tickFormatter={formatTime}
                domain={[minTime, maxTime]}
                type="category"
              />
              <YAxis domain={[0, 100]} />
              <ChartTooltip
                cursor={false}
                content={
                  <ChartTooltipContent
                    indicator="line"
                    labelFormatter={(value) => formatTime(value)}
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
