"use client";

import * as React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  Line,
  LineChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  fetchDeviceUptimeTimeseries,
  fetchDeviceUptimeStatus,
} from "@/lib/deviceMonitoring";
import {
  DeviceUptimeData,
  DeviceUptimeStatus,
  TimePeriodOption,
} from "@/lib/types";
import RingLoader from "react-spinners/RingLoader";
import { useAuth } from "@/context/authContext";

export const description =
  "Interactive charts showing device uptime over time with multiple visualizations";

type ChartType = "area" | "line" | "bar";

const DeviceUptimeCharts = () => {
  const { token } = useAuth();

  const timePeriodOptions: TimePeriodOption[] = [
    { label: "30 minutes", value: "30m" },
    { label: "60 minutes", value: "60m" },
    { label: "6 hours", value: "6h" },
    { label: "12 hours", value: "12h" },
    { label: "24 hours", value: "24h" },
    { label: "7 days", value: "7d" },
    { label: "30 days", value: "30d" },
  ];

  const [selectedDevice, setSelectedDevice] = React.useState<string>("");
  const [timePeriod, setTimePeriod] = React.useState(
    timePeriodOptions[2].value
  );
  const [chartType, setChartType] = React.useState<ChartType>("area");
  const [data, setData] = React.useState<DeviceUptimeData[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [devices, setDevices] = React.useState<DeviceUptimeStatus[]>([]);

  // Convert short format (5m, 15m, 60m, 6h, 24h, 7d, 30d) to backend format
  const convertPeriodToBackendFormat = (period: string): string => {
    const value = parseInt(period.slice(0, -1));
    const unit = period.slice(-1);

    const unitMap: Record<string, string> = {
      m: value === 1 ? "minute" : "minutes",
      h: value === 1 ? "hour" : "hours",
      d: value === 1 ? "day" : "days",
    };

    return `${value} ${unitMap[unit] || "hours"}`;
  };

  // Load devices on mount
  React.useEffect(() => {
    if (!token) return;

    const loadDevices = async () => {
      try {
        const devicesData = await fetchDeviceUptimeStatus(token);
        setDevices(devicesData);

        if (devicesData.length > 0) {
          setSelectedDevice(String(devicesData[0].device_id));
        }
      } catch (error) {
        console.error("Error fetching devices:", error);
        setDevices([]);
      }
    };

    loadDevices();
  }, [token]);

  // Load uptime data when device or period changes
  React.useEffect(() => {
    if (!token || !selectedDevice) return;

    const loadUptimeData = async () => {
      setIsLoading(true);
      try {
        const backendPeriod = convertPeriodToBackendFormat(timePeriod);
        const result = await fetchDeviceUptimeTimeseries(
          token,
          parseInt(selectedDevice),
          backendPeriod
        );
        setData(result);
      } catch (error) {
        console.error("Error fetching uptime data:", error);
        setData([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadUptimeData();
  }, [token, selectedDevice, timePeriod]);

  const chartData = React.useMemo(() => {
    // console.log('[CHART] Raw data from API:', data);
    const mapped = data.map((item) => {
      // Parse the timestamp and convert to readable format for display
      const timestamp = new Date(item.bucket);
      const displayDate = timestamp.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
      return {
        date: timestamp.getTime(), // Use timestamp for numeric x-axis positioning
        Time: displayDate, // Use readable label for tooltip
        "Uptime %": Number(item.uptime_percentage), // Use readable label for tooltip
        total_pings: item.total_pings,
      };
    });
    // console.log("[CHART] Mapped chart data:", mapped.slice(0, 3)); // Log first 3 items
    // console.log("[CHART] Chart data length:", mapped.length);
    return mapped;
  }, [data]);

  const renderChart = () => {
    switch (chartType) {
      case "area":
        return (
          <AreaChart
            accessibilityLayer
            data={chartData}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <defs>
              <linearGradient id="fillUptime" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#a855f7" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#a855f7" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={80}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
              }}
            />
            <YAxis
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tickFormatter={(tick) => `${tick}%`}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  indicator="line"
                  nameKey="Uptime %"
                  labelFormatter={(_, payload) => {
                    const item = payload?.[0]?.payload;
                    if (!item) return "—";
                    return (
                      item.Time ??
                      new Date(item.date).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })
                    );
                  }}
                />
              }
            />
            <Area
              dataKey="Uptime %"
              type="monotone"
              fill="url(#fillUptime)"
              fillOpacity={0.4}
              stroke="#a855f7"
              strokeWidth={2}
            />
          </AreaChart>
        );

      case "line":
        return (
          <LineChart
            accessibilityLayer
            data={chartData}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={80}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
              }}
            />
            <YAxis
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tickFormatter={(tick) => `${tick}%`}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  indicator="line"
                  nameKey="Uptime %"
                  labelFormatter={(_, payload) => {
                    const item = payload?.[0]?.payload;
                    if (!item) return "—";
                    return (
                      item.Time ??
                      new Date(item.date).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })
                    );
                  }}
                />
              }
            />
            <Line
              dataKey="Uptime %"
              type="monotone"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        );

      case "bar":
        return (
          <BarChart
            accessibilityLayer
            data={chartData}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={80}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                });
              }}
            />
            <YAxis
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              tickFormatter={(tick) => `${tick}%`}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  indicator="line"
                  nameKey="Uptime %"
                  labelFormatter={(_, payload) => {
                    const item = payload?.[0]?.payload;
                    if (!item) return "—";
                    return (
                      item.Time ??
                      new Date(item.date).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })
                    );
                  }}
                />
              }
            />
            <Bar dataKey="Uptime %" fill="#a855f7" radius={4} />
          </BarChart>
        );
    }
  };

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Device Uptime Timeline</CardTitle>
        <CardDescription className="mt-1">
          <span className="hidden @[540px]/card:block">
            Uptime percentage over time for the selected device
          </span>
        </CardDescription>
        <CardAction className="flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-sm font-medium text-foreground">
                Device:
              </label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger
                  className="w-full"
                  size="sm"
                  aria-label="Select device"
                  disabled={!devices.length}
                >
                  <SelectValue placeholder="Select device" />
                </SelectTrigger>
                <SelectContent className="rounded-xl bg-card border border-border">
                  {devices.map((device) => (
                    <SelectItem
                      key={device.device_id}
                      value={String(device.device_id)}
                      className="rounded-lg"
                    >
                      {device.device_name || `Device ${device.device_id}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-1.5 flex-1">
              <label className="text-sm font-medium text-foreground">
                Time Period:
              </label>
              <Select value={timePeriod} onValueChange={setTimePeriod}>
                <SelectTrigger
                  className="w-full"
                  size="sm"
                  aria-label="Select time period"
                >
                  <SelectValue placeholder="Select period" />
                </SelectTrigger>
                <SelectContent className="rounded-xl bg-card border border-border">
                  {timePeriodOptions.map((opt) => (
                    <SelectItem
                      key={opt.value}
                      value={opt.value}
                      className="rounded-lg"
                    >
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-foreground">
              Chart Type:
            </label>
            <Tabs
              value={chartType}
              onValueChange={(v) => setChartType(v as ChartType)}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="area">Area Chart</TabsTrigger>
                <TabsTrigger value="line">Line Chart</TabsTrigger>
                <TabsTrigger value="bar">Bar Chart</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center z-10 bg-background/50">
            <RingLoader color="var(--color-logo-orange)" size={48} />
          </div>
        )}

        <ChartContainer
          config={{
            "Uptime %": {
              label: "Uptime %",
              color: "#a855f7", // Visible purple
            },
          }}
          className="aspect-auto h-[400px] w-full"
        >
          {renderChart()}
        </ChartContainer>

        {isLoading && (
          <div className="text-center text-xs mt-2">Loading...</div>
        )}
        {!isLoading && devices.length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted-foreground text-sm">
              No monitored devices found.
            </p>
          </div>
        )}
        {!isLoading && devices.length > 0 && !chartData.length && (
          <div className="text-center text-xs mt-2">
            No data available for the selected period.
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceUptimeCharts;
