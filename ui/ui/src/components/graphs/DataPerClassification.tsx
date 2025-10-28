/**
 * File: DataPerClassification.tsx
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
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { fetchDataPerClassification } from "@/lib/networkData";
import { useLanguage } from "@/context/languageContext";
import { DataPerClassificationDataPoint } from "@/lib/types";

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

export default function DataPerClassification() {
  const { getT } = useLanguage();
  const [period, setPeriod] = useState("15 minutes");
  const [data, setData] = useState<DataPerClassificationDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetchDataPerClassification(token, period);
      // Convert bytes to megabytes (1e6) and round to two decimals
      const transformedData = Object.entries(response)
        .filter(([, bytes]) => bytes > 0) // Filter out zero values
        .map(([name, bytes]) => ({
          name,
          megabytes: Math.round((bytes / 1e6) * 100) / 100,
        }));
      setData(transformedData);
    } catch (err) {
      console.error("Error fetching data per classification:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
  };

  const getTimePeriodLabel = (value: string) => {
    return getT(`page.DataPerClassificationGraph.time_periods.${value}`, value);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT(
            "page.DataPerClassificationGraph.title",
            "Data Per Classification"
          )}
        </CardTitle>
        <CardDescription>
          View data usage by classification across all devices
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4 mb-6">
          {/* Time Period Control */}
          <div className="w-[200px]">
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
                  "page.DataPerClassificationGraph.loading",
                  "Loading classification data..."
                )}
              </span>
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground mb-2">
                {getT(
                  "page.DataPerClassificationGraph.no_data",
                  "No classification data available"
                )}
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
                  return (
                    <div className="border-border/50 bg-background grid min-w-[8rem] items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs shadow-xl">
                      <div className="font-medium">{label}</div>
                      <div className="flex items-center gap-2">
                        <div className="h-2.5 w-2.5 rounded-[2px] bg-primary"></div>
                        <span className="text-muted-foreground">
                          {getT(
                            "page.DataPerClassificationGraph.megabytes",
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
          Data usage by classification for {getTimePeriodLabel(period)}
        </div>
        <div className="text-muted-foreground leading-none">
          {data.length > 0 && `Total classifications: ${data.length}`}
        </div>
      </CardFooter>
    </Card>
  );
}
