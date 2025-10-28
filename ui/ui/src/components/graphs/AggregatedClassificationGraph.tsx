/**
 * File: AggregatedClassificationGraph.tsx
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
import { fetchHistoricalClassificationData } from "@/lib/networkData";
import { useLanguage } from "@/context/languageContext";
import { AggregatedClassificationDataPoint } from "@/lib/types";

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
  count: {
    label: "Count",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export default function AggregatedClassificationGraph() {
  const { getT } = useLanguage();
  const [period, setPeriod] = useState("1 day");
  const [data, setData] = useState<AggregatedClassificationDataPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAggregates = async (selectedPeriod: string) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await fetchHistoricalClassificationData(
        token,
        selectedPeriod
      );
      const transformedData = Object.entries(response).map(([name, count]) => ({
        name,
        count,
      }));
      setData(transformedData);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getAggregates(period);
  }, [period]);

  const handlePeriodChange = (value: string) => {
    setPeriod(value);
  };

  const getTimePeriodLabel = (value: string) => {
    return getT(
      `page.AggregatedClassificationGraph.time_periods.${value}`,
      value
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT("page.AggregatedClassificationGraph.title")}
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
                {getT("page.AggregatedClassificationGraph.loading")}
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
            <p className="text-muted-foreground">No data available</p>
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
                bottom: 60,
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
                        <span className="text-muted-foreground">Flows:</span>
                        <span className="text-foreground font-mono font-medium tabular-nums">
                          {data.value?.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  );
                }}
              />
              <Bar dataKey="count" fill="var(--color-count)" radius={8}>
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
          Showing classification data for {getTimePeriodLabel(period)}
        </div>
        <div className="text-muted-foreground leading-none">
          {data.length > 0 && `Total categories: ${data.length}`}
        </div>
      </CardFooter>
    </Card>
  );
}
