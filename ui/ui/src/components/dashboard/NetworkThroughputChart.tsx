"use client";

import { useEffect, useState, useMemo } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip } from "@/components/ui/chart";
import { useAuth } from "@/context/authContext";
import { fetchPortStatsAggregate } from "@/lib/portUtilization";
import { useLanguage } from "@/context/languageContext";
import { AggregateTimeSeriesPoint } from "@/lib/types";
import { TrendingUp, TrendingDown } from "lucide-react";

type TimeRange = "5min" | "1hour" | "24hour" | "7days";

interface NetworkThroughputChartProps {
  timeRange: TimeRange;
}

export default function NetworkThroughputChart({
  timeRange,
}: NetworkThroughputChartProps) {
  const { token } = useAuth();
  const { getT } = useLanguage();
  const [data, setData] = useState<AggregateTimeSeriesPoint[]>([]);
  const [previousPeriodTotal, setPreviousPeriodTotal] = useState<number | null>(null);
  const [isLoadingTrend, setIsLoadingTrend] = useState(false);

  // Calculate hours and interval based on time range
  const getTimeRangeParams = (range: TimeRange) => {
    switch (range) {
      case "5min":
        return { hours: 5 / 60, interval: "10 seconds" };
      case "1hour":
        return { hours: 1, interval: "1 minute" };
      case "24hour":
        return { hours: 24, interval: "5 minutes" };
      case "7days":
        return { hours: 168, interval: "1 hour" };
      default:
        return { hours: 1, interval: "1 minute" };
    }
  };

  // Calculate metrics from chart data
  const metrics = useMemo(() => {
    if (data.length === 0) {
      return {
        peak: 0,
        totalTransferred: 0,
      };
    }

    // Group by timestamp and sum throughputs (same logic as chart)
    const timeMap = new Map<number, number>();
    data.forEach((point) => {
      const ts = new Date(point.bucket_time).getTime();
      const throughput = point.avg_throughput ?? 0;
      timeMap.set(ts, (timeMap.get(ts) || 0) + throughput);
    });

    const aggregatedData = Array.from(timeMap.entries())
      .map(([ts, throughput]) => ({ ts, throughput }))
      .sort((a, b) => a.ts - b.ts);

    if (aggregatedData.length === 0) {
      return {
        peak: 0,
        totalTransferred: 0,
      };
    }

    // Peak throughput
    const peak = Math.max(...aggregatedData.map((d) => d.throughput));

    // Calculate total data transferred (sum of throughput * time interval)
    const { interval } = getTimeRangeParams(timeRange);
    let intervalSeconds = 60; // default 1 minute
    if (interval.includes("second")) {
      intervalSeconds = parseInt(interval.match(/\d+/)?.[0] || "10") || 10;
    } else if (interval.includes("minute")) {
      intervalSeconds = (parseInt(interval.match(/\d+/)?.[0] || "1") || 1) * 60;
    } else if (interval.includes("hour")) {
      intervalSeconds = (parseInt(interval.match(/\d+/)?.[0] || "1") || 1) * 3600;
    }

    // Sum throughput * interval to get total bytes
    // Throughput is in Mbps, convert to bytes: Mbps * 125000 bytes/sec * seconds
    const totalBytes = aggregatedData.reduce(
      (sum, d) => sum + (d.throughput * 125000 * intervalSeconds),
      0
    );

    return {
      peak,
      totalTransferred: totalBytes,
    };
  }, [data, timeRange]);

  // Get time period label for trend text
  const getTimePeriodLabel = (range: TimeRange): string => {
    switch (range) {
      case "5min":
        return "last 5 minutes";
      case "1hour":
        return "last hour";
      case "24hour":
        return "last 24 hours";
      case "7days":
        return "last 7 days";
      default:
        return "last hour";
    }
  };

  // Calculate trend percentage
  const trend = useMemo(() => {
    if (!previousPeriodTotal || metrics.totalTransferred === 0 || previousPeriodTotal === 0) {
      return null;
    }

    const change = ((metrics.totalTransferred - previousPeriodTotal) / previousPeriodTotal) * 100;
    return {
      percentage: Math.abs(change),
      isPositive: change >= 0,
    };
  }, [metrics.totalTransferred, previousPeriodTotal]);

  // Format bytes to human-readable format
  const formatBytes = (bytes: number): string => {
    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  // Format throughput to Kbps/Mbps/Gbps automatically
  const formatThroughput = (mbps: number): string => {
    if (mbps >= 1000) {
      return `${(mbps / 1000).toFixed(1)} Gbps`;
    } else if (mbps < 1) {
      return `${(mbps * 1000).toFixed(1)} Kbps`;
    }
    return `${mbps.toFixed(1)} Mbps`;
  };

  // Get the appropriate unit for the Y-axis based on data range
  const getYAxisUnit = (): { unit: string; formatter: (val: number) => string } => {
    if (data.length === 0) {
      return { unit: "Mbps", formatter: (v) => `${v.toFixed(0)}` };
    }

    // Find max value in aggregated data
    const timeMap = new Map<number, number>();
    data.forEach((point) => {
      const ts = new Date(point.bucket_time).getTime();
      const throughput = point.avg_throughput ?? 0;
      timeMap.set(ts, (timeMap.get(ts) || 0) + throughput);
    });
    const maxValue = Math.max(...Array.from(timeMap.values()));

    if (maxValue >= 1000) {
      return {
        unit: "Gbps",
        formatter: (v) => `${(v / 1000).toFixed(1)}`,
      };
    } else if (maxValue < 1) {
      return {
        unit: "Kbps",
        formatter: (v) => `${(v * 1000).toFixed(0)}`,
      };
    }
    return {
      unit: "Mbps",
      formatter: (v) => `${v.toFixed(0)}`,
    };
  };

  const yAxisConfig = getYAxisUnit();

  useEffect(() => {
    if (!token) return;
    
    // Reset previous period total when time range changes to prevent flickering
    setPreviousPeriodTotal(null);
    setIsLoadingTrend(true);
    
    const load = async () => {
      try {
        const { hours, interval } = getTimeRangeParams(timeRange);
        
        // Fetch both current and previous period data in parallel
        const [currentRes, previousRes] = await Promise.all([
          fetchPortStatsAggregate(token, null, hours, interval),
          fetchPortStatsAggregate(token, null, hours * 2, interval).catch(() => null),
        ]);
        
        if (currentRes && currentRes.aggregated_data) {
          console.log("[NetworkThroughputChart] Received data:", currentRes.aggregated_data.length, "points");
          setData(currentRes.aggregated_data);
          
          // Calculate interval seconds
          let intervalSeconds = 60;
          if (interval.includes("second")) {
            intervalSeconds = parseInt(interval.match(/\d+/)?.[0] || "10") || 10;
          } else if (interval.includes("minute")) {
            intervalSeconds = (parseInt(interval.match(/\d+/)?.[0] || "1") || 1) * 60;
          } else if (interval.includes("hour")) {
            intervalSeconds = (parseInt(interval.match(/\d+/)?.[0] || "1") || 1) * 3600;
          }
          
          // Calculate previous period total if we have the data
          if (previousRes && previousRes.aggregated_data) {
            const allData = previousRes.aggregated_data;
            const sortedByTime = [...allData].sort(
              (a, b) => new Date(a.bucket_time).getTime() - new Date(b.bucket_time).getTime()
            );
            
            if (sortedByTime.length > 0) {
              const midpoint = sortedByTime[Math.floor(sortedByTime.length / 2)];
              const midpointTime = new Date(midpoint.bucket_time).getTime();
              
              // Get previous period data (first half)
              const previousPeriodData = sortedByTime.filter(
                (point) => new Date(point.bucket_time).getTime() < midpointTime
              );
              
              const prevTimeMap = new Map<number, number>();
              previousPeriodData.forEach((point) => {
                const ts = new Date(point.bucket_time).getTime();
                const throughput = point.avg_throughput ?? 0;
                prevTimeMap.set(ts, (prevTimeMap.get(ts) || 0) + throughput);
              });
              
              const previousTotal = Array.from(prevTimeMap.values()).reduce(
                (sum, throughput) => sum + (throughput * 125000 * intervalSeconds),
                0
              );
              
              // Set both values together to prevent flickering
              setPreviousPeriodTotal(previousTotal);
              setIsLoadingTrend(false);
            } else {
              setPreviousPeriodTotal(null);
              setIsLoadingTrend(false);
            }
          } else {
            setPreviousPeriodTotal(null);
            setIsLoadingTrend(false);
          }
        } else {
          console.warn("[NetworkThroughputChart] No data in response:", currentRes);
          setData([]);
          setPreviousPeriodTotal(null);
          setIsLoadingTrend(false);
        }
      } catch (error) {
        console.error("[NetworkThroughputChart] Error fetching data:", error);
        setData([]);
        setPreviousPeriodTotal(null);
        setIsLoadingTrend(false);
      }
    };
    load();
    // Refresh interval based on time range (shorter for shorter ranges)
    const refreshInterval = timeRange === "5min" ? 30000 : timeRange === "1hour" ? 60000 : 300000; // 30s, 1min, or 5min
    const interval = setInterval(load, refreshInterval);
    return () => clearInterval(interval);
  }, [token, timeRange]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT(
            "dashboard.throughput",
            "Total Network Throughput (Port Utilization)"
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No throughput data available.
            </div>
        ) : (
        <>
          {/* Summary Metrics */}
          <div className="mb-6 grid grid-cols-2 gap-4">
            {/* Total Data Transferred */}
            <div>
              <div className="text-sm text-muted-foreground">
                Total Data Transferred
              </div>
              <div className="text-2xl font-semibold text-[#a855f7]">
                {formatBytes(metrics.totalTransferred)}
              </div>
              {!isLoadingTrend && trend !== null && (
                <div
                  className={`flex items-center gap-1 text-sm mt-1 ${
                    trend.isPositive ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {trend.isPositive ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  <span className="text-muted-foreground">
                    {trend.isPositive ? "+" : "-"}
                    {trend.percentage.toFixed(1)}% from {getTimePeriodLabel(timeRange)}
                  </span>
                </div>
              )}
            </div>

            {/* Peak Throughput */}
            <div>
              <div className="text-sm text-muted-foreground">Peak</div>
              <div className="text-2xl font-semibold">
                {formatThroughput(metrics.peak)}
              </div>
            </div>
          </div>
          <ChartContainer
          config={{
            throughput: { label: "Mbps", color: "#a855f7" },
          }}
          className="h-[300px] w-full"
        >
          <AreaChart
            accessibilityLayer
            data={(() => {
              // Group by timestamp and sum all port throughputs to get network total
              const timeMap = new Map<number, number>();
              data.forEach((point) => {
                const ts = new Date(point.bucket_time).getTime();
                const throughput = point.avg_throughput ?? 0;
                timeMap.set(ts, (timeMap.get(ts) || 0) + throughput);
              });
              
              return Array.from(timeMap.entries())
                .map(([ts, throughput]) => ({ ts, throughput }))
                .sort((a, b) => a.ts - b.ts);
            })()}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <defs>
              <linearGradient id="fillThroughput" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="ts"
              type="number"
              scale="time"
              domain={["dataMin", "dataMax"]}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={80}
              tickFormatter={(v) =>
                new Date(v).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              label={{
                value: yAxisConfig.unit,
                angle: -90,
                position: "insideLeft",
              }}
              tickFormatter={yAxisConfig.formatter}
            />
            <ChartTooltip
              cursor={false}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const value = payload[0]?.value;
                const ts = payload[0]?.payload?.ts;
                const throughputValue = typeof value === "number" ? value : 0;
                return (
                  <div className="rounded-lg border bg-background p-2 shadow-sm">
                    <p className="text-sm font-medium mb-2">
                      {ts ? new Date(ts).toLocaleString() : ""}
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      <span className="font-medium">Throughput:</span>
                      <span className="font-mono">
                        {formatThroughput(throughputValue)}
                      </span>
                    </div>
                  </div>
                );
              }}
            />
            <Area
              dataKey="throughput"
              type="monotone"
              strokeWidth={2}
              stroke="#a855f7"
              fill="url(#fillThroughput)"
              fillOpacity={0.4}
              isAnimationActive={false}
            />
          </AreaChart>
        </ChartContainer>
        </>
        )}
      </CardContent>
    </Card>
  );
}

