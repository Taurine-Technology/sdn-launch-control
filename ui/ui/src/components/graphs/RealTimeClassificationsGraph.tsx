"use client";

import React, { useState, useEffect } from "react";
import { Bar, BarChart, CartesianGrid, LabelList, XAxis } from "recharts";
import { TrendingUp, Wifi, Activity } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
} from "@/components/ui/chart";
import { useMultiWebSocket } from "@/context/MultiWebSocketContext";
import { useLanguage } from "@/context/languageContext";
import { ClassificationMessage, WebSocketMessage } from "@/lib/types";

interface ClassificationDataPoint {
  name: string;
  value: number;
}

const chartConfig = {
  value: {
    label: "Count",
    color: "var(--chart-1)",
  },
} satisfies ChartConfig;

export default function RealTimeClassificationsGraph() {
  const { getT } = useLanguage();
  const [classificationData, setClassificationData] = useState<
    ClassificationDataPoint[]
  >([]);
  const { subscribe } = useMultiWebSocket();

  useEffect(() => {
    const handleMessage = (data: WebSocketMessage) => {
      // Handle the raw flow data format that's actually coming from the WebSocket
      if (typeof data === "string") {
        try {
          const parsedData = JSON.parse(data);
          if (parsedData.flow) {
            updateClassificationData(parsedData.flow);
            return;
          }
        } catch (error) {
          console.error("Failed to parse classification data as JSON:", error);
        }
      }

      // Handle the object format that's actually coming from the WebSocket
      if (typeof data === "object" && data !== null && "flow" in data) {
        const flowData = data as unknown as { flow: string };
        updateClassificationData(flowData.flow);
        return;
      }

      // Handle the expected ClassificationMessage format as fallback
      if (
        data.type === "classification" &&
        (data as ClassificationMessage).data?.classification
      ) {
        updateClassificationData(
          (data as ClassificationMessage).data.classification
        );
      } else {
        console.error("Invalid or missing classification data", data);
      }
    };

    // Subscribe to the classification endpoint
    const unsubscribe = subscribe("classifications", handleMessage);

    return () => {
      unsubscribe();
    };
  }, [subscribe]);

  const updateClassificationData = (categoryName: string) => {
    setClassificationData((prevData) => {
      const newData = [...prevData];
      const index = newData.findIndex((data) => data.name === categoryName);
      if (index !== -1) {
        newData[index].value += 1;
      } else {
        newData.push({ name: categoryName, value: 1 });
      }
      return newData;
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{getT("page.RealTimeClassificationsGraph.title")}</CardTitle>
        <CardDescription>
          {getT("page.RealTimeClassificationsGraph.description")}
        </CardDescription>
      </CardHeader>
      <CardContent className="w-full">
        {classificationData.length === 0 ? (
          <div className="flex items-center justify-center min-h-[300px] max-h-[400px]">
            <div className="text-center max-w-md">
              <div className="flex justify-center mb-4">
                <div className="relative">
                  <Wifi className="h-12 w-12 text-muted-foreground/60" />
                  <Activity className="h-6 w-6 text-primary absolute -top-1 -right-1 animate-pulse" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-2">
                {getT(
                  "page.RealTimeClassificationsGraph.waiting_title",
                  "Monitoring Network Traffic"
                )}
              </h3>
              <p className="text-muted-foreground mb-3">
                {getT("page.RealTimeClassificationsGraph.waiting_message")}
              </p>
              <div className="bg-muted/50 rounded-lg p-3 text-sm">
                <p className="text-muted-foreground mb-1">
                  {getT(
                    "page.RealTimeClassificationsGraph.status_connected",
                    "✓ WebSocket Connected"
                  )}
                </p>
                <p className="text-muted-foreground">
                  {getT(
                    "page.RealTimeClassificationsGraph.status_waiting",
                    "Waiting for network traffic to be classified..."
                  )}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <ChartContainer
            config={chartConfig}
            className="min-h-[300px] max-h-[400px] w-full"
          >
            <BarChart
              accessibilityLayer
              data={classificationData}
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
                        <span className="text-muted-foreground">flows</span>
                        <span className="text-foreground font-mono font-medium tabular-nums">
                          {data.value?.toLocaleString()}
                        </span>
                      </div>
                    </div>
                  );
                }}
              />
              <Bar dataKey="value" fill="var(--color-value)" radius={8}>
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
          Real-time classification data
        </div>
        <div className="text-muted-foreground leading-none">
          {classificationData.length > 0 &&
            `Total categories: ${classificationData.length}`}
        </div>
      </CardFooter>
    </Card>
  );
}
