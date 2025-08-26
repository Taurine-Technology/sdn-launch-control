"use client";

import React, { useEffect, useState, useCallback } from "react";
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
import { Input } from "@/components/ui/input";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { fetchUserFlowData } from "@/lib/networkData";
import { fetchNetworkDevices } from "@/lib/devices";
import { useLanguage } from "@/context/languageContext";
import {
  UserFlowData,
  UserFlowDataPoint,
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

export default function UserDataUsageGraph() {
  const { getT } = useLanguage();
  const [period, setPeriod] = useState("15 minutes");
  const [searchQuery, setSearchQuery] = useState("");
  const [allData, setAllData] = useState<UserFlowData>({});
  const [chartData, setChartData] = useState<UserFlowDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [devices, setDevices] = useState<NetworkDeviceDetails[]>([]);
  const [filteredDevices, setFilteredDevices] = useState<
    NetworkDeviceDetails[]
  >([]);
  const [selectedMacAddress, setSelectedMacAddress] = useState("");
  const [isDeviceSelected, setIsDeviceSelected] = useState(false);

  const fetchDevices = async () => {
    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) return;

      const devicesData = await fetchNetworkDevices(token);
      const deviceArr = Array.isArray(devicesData)
        ? devicesData
        : devicesData.results || [];
      setDevices(deviceArr);
    } catch (err) {
      console.error("Error fetching devices:", err);
    }
  };

  const fetchUserFlowDataHandler = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const data = await fetchUserFlowData(token, period);
      setAllData(data);

      // If there are MAC addresses and none is selected, pick the first one
      const macAddresses = Object.keys(data);
      if (macAddresses.length > 0 && !selectedMacAddress) {
        setSelectedMacAddress(macAddresses[0]); // Select first MAC address
      }
    } catch (err) {
      console.error("Error fetching user flow data:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [period, selectedMacAddress]);

  useEffect(() => {
    fetchDevices();
  }, []);

  useEffect(() => {
    fetchUserFlowDataHandler();
  }, [fetchUserFlowDataHandler]);

  useEffect(() => {
    if (!searchQuery.trim() || isDeviceSelected) {
      setFilteredDevices([]);
      return;
    }

    const filtered = devices.filter((device) => {
      const query = searchQuery.toLowerCase();
      return (
        device.name?.toLowerCase().includes(query) ||
        device.mac_address?.toLowerCase().includes(query) ||
        device.ip_address?.toLowerCase().includes(query)
      );
    });
    setFilteredDevices(filtered.slice(0, 5)); // Limit to 5 results
  }, [searchQuery, devices, isDeviceSelected]);

  // Update chart data when a MAC address is selected
  useEffect(() => {
    if (selectedMacAddress && allData[selectedMacAddress]) {
      const macData = allData[selectedMacAddress];
      const transformed = Object.entries(macData)
        .filter(([, bytes]) => bytes > 0) // Filter out zero values
        .map(([name, bytes]) => ({
          name,
          megabytes: Math.round((bytes / 1e6) * 100) / 100,
        }));
      setChartData(transformed);
    } else {
      setChartData([]);
    }
  }, [selectedMacAddress, allData]);

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
  };

  const handleDeviceSelect = (device: NetworkDeviceDetails) => {
    setSelectedMacAddress(device.mac_address);
    setSearchQuery(device.name || device.mac_address);
    setFilteredDevices([]); // Clear dropdown immediately
    setIsDeviceSelected(true); // Mark device as selected to prevent dropdown from showing
  };

  const getTimePeriodLabel = (value: string) => {
    return getT(`page.UserDataUsageGraph.time_periods.${value}`, value);
  };

  const getSelectedDeviceInfo = () => {
    return devices.find((device) => device.mac_address === selectedMacAddress);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT("page.UserDataUsageGraph.title", "User Data Usage")}
        </CardTitle>
        <CardDescription>
          Search for a device and view its data usage by classification
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4 mb-6">
          {/* Search and Controls */}
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className="text-sm font-medium mb-2 block">
                Search Device
              </label>
              <div className="relative">
                <Input
                  placeholder="Search by name, MAC, or IP address"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setIsDeviceSelected(false); // Reset selection state when user starts typing
                  }}
                  className="pr-10"
                />
                {filteredDevices.length > 0 && (
                  <div className="absolute top-full left-0 right-0 bg-background border rounded-md shadow-lg z-10 max-h-60 overflow-y-auto">
                    {filteredDevices.map((device) => (
                      <button
                        key={device.id}
                        className="w-full text-left px-3 py-2 hover:bg-accent hover:text-accent-foreground border-b last:border-b-0"
                        onClick={() => handleDeviceSelect(device)}
                      >
                        <div className="font-medium">
                          {device.name || "Unnamed Device"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {device.mac_address} • {device.ip_address || "No IP"}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="w-[180px]">
              <label className="text-sm font-medium mb-2 block">
                Time Period
              </label>
              <Select value={period} onValueChange={handlePeriodChange}>
                <SelectTrigger>
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
          </div>

          {/* Selected Device Info */}
          {selectedMacAddress && (
            <div className="p-3 bg-muted rounded-md">
              <div className="text-sm font-medium mb-1">Selected Device:</div>
              <div className="text-sm text-muted-foreground">
                {getSelectedDeviceInfo()?.name || "Unnamed Device"} •{" "}
                {selectedMacAddress}
              </div>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-destructive text-sm">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span className="text-muted-foreground">
                {getT(
                  "page.UserDataUsageGraph.loading",
                  "Loading data usage..."
                )}
              </span>
            </div>
          </div>
        ) : chartData.length === 0 && selectedMacAddress ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground mb-2">
                {getT(
                  "page.UserDataUsageGraph.no_data",
                  "No data usage available for this device"
                )}
              </p>
            </div>
          </div>
        ) : !selectedMacAddress ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground mb-2">
                Search for a device to view data usage
              </p>
            </div>
          </div>
        ) : (
          <ChartContainer
            config={chartConfig}
            className="min-h-[300px] max-h-[400px] w-full"
          >
            <BarChart
              accessibilityLayer
              data={chartData}
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
                  value && value.length > 10
                    ? `${value.substring(0, 10)}...`
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
                  return (
                    <div className="border-border/50 bg-background grid min-w-[8rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl">
                      <div className="font-medium">{label}</div>
                      <div className="flex items-center gap-2">
                        <div className="h-2.5 w-2.5 rounded-[2px] bg-primary"></div>
                        <span className="text-muted-foreground">
                          {getT(
                            "page.UserDataUsageGraph.megabytes",
                            "Megabytes"
                          )}
                          :
                        </span>
                        <span className="text-foreground font-mono font-medium tabular-nums">
                          {data.value?.toLocaleString()}
                        </span>
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
          {chartData.length > 0 && `Total classifications: ${chartData.length}`}
        </div>
      </CardFooter>
    </Card>
  );
}
