"use client";

import * as React from "react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Cell } from "recharts";
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
import { 
  fetchDeviceUptimeAggregates,
  fetchDeviceUptimeStatus 
} from "@/lib/deviceMonitoring";
import { 
  DeviceAggregationData, 
  DeviceUptimeStatus, 
  ChartDataPoint,
  TimePeriodOption 
} from "@/lib/types";
import RingLoader from "react-spinners/RingLoader";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";

export const description = "An interactive bar chart showing device uptime overview";

const DeviceUptimeOverview = () => {
  const { getT } = useLanguage();
  const { token } = useAuth();

  const timePeriodOptions: TimePeriodOption[] = [
    { label: "5 minutes", value: "5m" },
    { label: "15 minutes", value: "15m" },
    { label: "60 minutes", value: "60m" },
    { label: "6 hours", value: "6h" },
    { label: "12 hours", value: "12h" },
    { label: "24 hours", value: "24h" },
    { label: "7 days", value: "7d" },
    { label: "30 days", value: "30d" },
  ];

  const [timePeriod, setTimePeriod] = React.useState(timePeriodOptions[2].value); // Default to 60m
  const [aggregationData, setAggregationData] = React.useState<DeviceAggregationData[]>([]);
  const [devices, setDevices] = React.useState<DeviceUptimeStatus[]>([]);
  const [loading, setLoading] = React.useState(false);

  // Convert short format (5m, 1h, 7d) to backend format ("5 minutes", "1 hour", "7 days")
  const convertPeriodToBackendFormat = (period: string): string => {
    const value = parseInt(period.slice(0, -1));
    const unit = period.slice(-1);
    
    const unitMap: Record<string, string> = {
      'm': value === 1 ? 'minute' : 'minutes',
      'h': value === 1 ? 'hour' : 'hours',
      'd': value === 1 ? 'day' : 'days'
    };
    
    return `${value} ${unitMap[unit] || 'minutes'}`;
  };

  const loadData = React.useCallback(async () => {
    if (!token) return;

    setLoading(true);
    try {
      const backendPeriod = convertPeriodToBackendFormat(timePeriod);
      const [aggData, devicesData] = await Promise.all([
        fetchDeviceUptimeAggregates(token, backendPeriod, 1),
        fetchDeviceUptimeStatus(token),
      ]);

      console.log('[OVERVIEW] Raw aggregation data:', aggData);
      console.log('[OVERVIEW] Devices data:', devicesData);
      setAggregationData(aggData);
      setDevices(devicesData);
    } catch (error) {
      console.error("Error fetching data:", error);
      setAggregationData([]);
      setDevices([]);
    }
    setLoading(false);
  }, [timePeriod, token]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const getBarColor = (uptimePercentage: number): string => {
    if (uptimePercentage > 95) {
      return "#22c55e"; // Green
    } else if (uptimePercentage > 80) {
      return "#eab308"; // Yellow
    } else {
      return "#ef4444"; // Red
    }
  };

  const chartData: ChartDataPoint[] = React.useMemo(() => {
    if (!aggregationData || aggregationData.length === 0) return [];

    // The backend now includes device_name directly in aggregation data
    // Map each aggregation record to the chart data format
    const mapped = aggregationData.map((item) => ({
      name: item.device_name || `Device ${item.device_id}`,
      "Uptime": item.uptime_percentage, // Use readable label for tooltip
      total_pings: item.total_pings,
      device_id: item.device_id,
      fill: getBarColor(item.uptime_percentage), // Add color for tooltip
    }));
    
    console.log('[OVERVIEW] Chart data:', mapped);
    return mapped;
  }, [aggregationData]);

  const t = React.useCallback((key: string) => getT(`deviceMonitoring.overview.${key}`), [getT]);

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>
          <span className="hidden @[540px]/card:block">
            {t("description")}
          </span>
        </CardDescription>
        <CardAction className="flex flex-col gap-2 sm:flex-row sm:gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-muted-foreground whitespace-nowrap">
              Time Period:
            </label>
            <Select value={timePeriod} onValueChange={setTimePeriod}>
              <SelectTrigger
                className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate"
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
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <RingLoader color="var(--color-logo-orange)" size={48} />
          </div>
        )}
        <ChartContainer
          config={{
            Uptime: {
              label: "Uptime %",
              color: "#22c55e",
            },
          }}
          className="aspect-auto h-[400px] w-full"
        >
          <BarChart data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              label={{ value: "Device Name", position: "insideBottom", offset: -5, style: { fontSize: "12px", fill: "#888" } }}
              tickFormatter={(value) => {
                return value && value.length > 10
                  ? `${value.substring(0, 10)}...`
                  : value;
              }}
            />
            <YAxis
              domain={[0, 100]}
              tickLine={false}
              axisLine={false}
              label={{ value: "Uptime Percentage (%)", angle: -90, position: "insideLeft", style: { fontSize: "12px", fill: "#888" } }}
              tickFormatter={(tick) => `${tick}%`}
            />
            <ChartTooltip
              content={<ChartTooltipContent indicator="line" nameKey="Uptime" />}
            />
            <Bar dataKey="Uptime" name="Uptime %">
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarColor(entry.Uptime)}
                />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
        {loading && <div className="text-center text-xs mt-2">{t("loading")}</div>}
        {!loading && devices.length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted-foreground text-sm">
              {t("noDevices")}
            </p>
          </div>
        )}
        {!loading && devices.length > 0 && !chartData.length && (
          <div className="text-center text-xs mt-2">{t("noData")}</div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceUptimeOverview;
