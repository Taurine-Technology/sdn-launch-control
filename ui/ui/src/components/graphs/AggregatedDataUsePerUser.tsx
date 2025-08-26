"use client";

import React, { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, LabelList, XAxis } from "recharts";
import { TrendingUp } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { fetchAggregateFlowsByUser } from "@/lib/networkData";
import { fetchNetworkDevices } from "@/lib/devices";
import { useLanguage } from "@/context/languageContext";
import {
  AggregatedDataPerUserDataPoint,
  DeviceMetaData,
  NetworkDeviceDetails,
} from "@/lib/types";

const timePeriods = [
  { value: "15 minutes", label: "15 minutes" },
  { value: "1 hour", label: "1 hour" },
  { value: "3 hours", label: "3 hours" },
  { value: "8 hours", label: "8 hours" },
  { value: "12 hours", label: "12 hours" },
  { value: "1 day", label: "1 day" },
  { value: "7 days", label: "7 days" },
  { value: "30 days", label: "30 days" },
];

const chartConfig = {
  megabytes: {
    label: "Megabytes",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export default function AggregatedDataUsePerUser() {
  const { getT } = useLanguage();
  const [period, setPeriod] = useState("1 hour");
  const [data, setData] = useState<AggregatedDataPerUserDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deviceMeta, setDeviceMeta] = useState<DeviceMetaData>({});

  const getAggregates = async (selectedPeriod: string) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetchAggregateFlowsByUser(token, selectedPeriod);
      const transformedData = Object.entries(response).map(
        ([mac, totalBytes]) => ({
          name: mac,
          megabytes: Math.round((totalBytes / 1e6) * 100) / 100,
        })
      );
      setData(transformedData);
    } catch (err) {
      console.error("Error fetching user aggregates:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  const fetchDeviceMeta = async () => {
    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) return;

      const devices = await fetchNetworkDevices(token);
      const deviceArr = Array.isArray(devices)
        ? devices
        : devices.results || [];
      const metaMap: DeviceMetaData = {};

      deviceArr.forEach((dev: NetworkDeviceDetails) => {
        if (dev.mac_address) {
          metaMap[dev.mac_address.toLowerCase()] = dev;
        }
      });

      setDeviceMeta(metaMap);
    } catch (err) {
      console.error("Error fetching device metadata:", err);
      setDeviceMeta({});
    }
  };

  useEffect(() => {
    getAggregates(period);
  }, [period]);

  useEffect(() => {
    fetchDeviceMeta();
  }, []);

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
  };

  const getTimePeriodLabel = (value: string) => {
    return getT(`page.AggregatedDataUsePerUser.time_periods.${value}`, value);
  };

  const getDeviceInfo = (macAddress: string) => {
    const meta = deviceMeta[macAddress.toLowerCase()];
    return {
      name: meta?.name || getT("page.DevicesPage.unknown", "Unknown"),
      deviceType:
        meta?.device_type || getT("page.DevicesPage.unknown", "Unknown"),
      ipAddress:
        meta?.ip_address || getT("page.DevicesPage.unknown", "Unknown"),
    };
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT("page.AggregatedDataUsePerUser.title", "Data Usage Per User")}
        </CardTitle>
        <CardDescription>
          <div className="flex items-center gap-4">
            <span>Time Period:</span>
            <Select value={period} onValueChange={handlePeriodChange}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Select time period" />
              </SelectTrigger>
              <SelectContent>
                {timePeriods.map((periodOption) => (
                  <SelectItem
                    key={periodOption.value}
                    value={periodOption.value}
                  >
                    {getTimePeriodLabel(periodOption.value)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span className="text-muted-foreground">
                {getT(
                  "page.AggregatedDataUsePerUser.loading",
                  "Loading data..."
                )}
              </span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="text-center">
              <p className="text-destructive mb-2">Error loading data</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <p className="text-muted-foreground">
              {getT(
                "page.AggregatedDataUsePerUser.no_data",
                "No data available"
              )}
            </p>
          </div>
        ) : (
          <ChartContainer
            config={chartConfig}
            className="min-h-[300px] max-h-[400px] w-full"
          >
            <BarChart
              accessibilityLayer
              data={data}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 80,
              }}
              height={350}
            >
              <CartesianGrid vertical={false} />
              <XAxis
                dataKey="name"
                tickLine={false}
                tickMargin={20}
                axisLine={false}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={40}
                tickFormatter={(value) =>
                  value && value.length > 12
                    ? `${value.substring(0, 12)}...`
                    : value
                }
              />
              <ChartTooltip
                cursor={false}
                content={({ active, payload, label }) => {
                  if (!active || !payload || !payload.length) {
                    return null;
                  }

                  const data = payload[0];
                  const deviceInfo = getDeviceInfo(label);

                  return (
                    <div className="border-border/50 bg-background grid min-w-[12rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl">
                      <div className="font-medium">
                        {getT("page.DevicesPage.mac_address", "MAC Address")}:{" "}
                        {label}
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-2.5 w-2.5 rounded-[2px] bg-primary"></div>
                        <span className="text-muted-foreground">
                          {getT(
                            "page.AggregatedDataUsePerUser.megabytes",
                            "Megabytes"
                          )}
                          :
                        </span>
                        <span className="text-foreground font-mono font-medium tabular-nums">
                          {data.value?.toLocaleString()}
                        </span>
                      </div>
                      <div className="text-muted-foreground">
                        {getT("page.DevicesPage.name", "Name")}:{" "}
                        {deviceInfo.name}
                      </div>
                      <div className="text-muted-foreground">
                        {getT("page.DevicesPage.device_type", "Device Type")}:{" "}
                        {deviceInfo.deviceType}
                      </div>
                      <div className="text-muted-foreground">
                        {getT("page.DevicesPage.ip_address", "IP Address")}:{" "}
                        {deviceInfo.ipAddress}
                      </div>
                    </div>
                  );
                }}
              />
              <Bar dataKey="megabytes" fill="var(--color-megabytes)" radius={8}>
                <LabelList
                  position="top"
                  offset={12}
                  className="fill-foreground"
                  fontSize={12}
                />
              </Bar>
            </BarChart>
          </ChartContainer>
        )}
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="flex gap-2 leading-none font-medium">
          <TrendingUp className="h-4 w-4" />
          Data usage for {getTimePeriodLabel(period)}
        </div>
        <div className="text-muted-foreground leading-none">
          {data.length > 0 && `Total devices: ${data.length}`}
        </div>
      </CardFooter>
    </Card>
  );
}
