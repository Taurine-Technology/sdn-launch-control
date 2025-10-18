"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/authContext";
import { useLanguage } from "@/context/languageContext";
import { getClassificationStats } from "@/lib/classifier";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import ProtectedRoute from "@/lib/ProtectedRoute";

interface ClassificationData {
  name: string;
  count: number;
  percentage: number;
  color: string;
}

const chartConfig = {
  count: {
    label: "Classifications",
    color: "hsl(var(--chart-1))",
  },
} satisfies ChartConfig;

export default function ClassificationConfidencePage() {
  const { token } = useAuth();
  const { getT } = useLanguage();
  const t = (key: string) => getT(`aiServices.classificationConfidence.${key}`);

  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedHours, setSelectedHours] = useState<string>("720");
  const [loading, setLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chartData, setChartData] = useState<ClassificationData[]>([]);
  const [totalClassifications, setTotalClassifications] = useState<number>(0);
  const [avgPredictionTime, setAvgPredictionTime] = useState<number>(0);
  const [availableModels, setAvailableModels] = useState<Array<{name: string, display_name: string, is_active: boolean}>>([]);


  useEffect(() => {
    if (token) {
      fetchModels();
    }
  }, [token]);

  useEffect(() => {
    if (token && selectedModel) {
      fetchData();
    }
  }, [token, selectedModel, selectedHours]);

  const fetchModels = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/v1/models/", {
        headers: {
          "Authorization": `Token ${token}`,
          "Content-Type": "application/json",
        },
      });
      const data = await response.json();
      if (data.status === "success" && data.models) {
        setAvailableModels(data.models);
        // Set the active model as default
        const activeModel = data.models.find((model: any) => model.is_active);
        if (activeModel) {
          setSelectedModel(activeModel.name);
        }
      }
    } catch (err) {
      console.error("Error fetching models:", err);
    }
  };

  const fetchData = async () => {
    if (!token) return;
    
    setChartLoading(true);
    setError(null);
    
    try {
      // Use real API call
      const stats = await getClassificationStats(token, {
        model_name: selectedModel || undefined,
        hours: parseInt(selectedHours),
        summary: true,
      });

      // Check if we have summary data (when summary=true)
      if (stats.data?.summary && stats.data.summary.confidence_breakdown) {
        const breakdown = stats.data.summary.confidence_breakdown;
        const total = stats.data.summary.total_classifications || 0;
        const avgTime = stats.data.summary.avg_prediction_time_ms || 0;

        setTotalClassifications(total);
        setAvgPredictionTime(avgTime);

        const data = [
          { 
            name: t("highConfidence"), 
            count: breakdown.high_confidence?.count || 0, 
            percentage: breakdown.high_confidence?.percentage || 0,
            color: "var(--chart-1)"
          },
          { 
            name: t("lowConfidence"), 
            count: breakdown.low_confidence?.count || 0, 
            percentage: breakdown.low_confidence?.percentage || 0,
            color: "var(--chart-2)"
          },
          { 
            name: t("multipleCandidates"), 
            count: breakdown.multiple_candidates?.count || 0, 
            percentage: breakdown.multiple_candidates?.percentage || 0,
            color: "var(--chart-3)"
          },
          { 
            name: t("uncertain"), 
            count: breakdown.uncertain?.count || 0, 
            percentage: breakdown.uncertain?.percentage || 0,
            color: "var(--chart-4)"
          },
        ];

        setChartData(data);
      }
      // Fallback: Check if we have periods data (when summary=false)
      else if (stats.data?.periods && Array.isArray(stats.data.periods)) {
        // Aggregate data from all periods
        let totalHigh = 0;
        let totalLow = 0;
        let totalMultiple = 0;
        let totalUncertain = 0;
        let totalClassifications = 0;
        let totalPredictionTime = 0;
        let periodCount = 0;

        stats.data.periods.forEach((period: any) => {
          totalHigh += period.high_confidence_count || 0;
          totalLow += period.low_confidence_count || 0;
          totalMultiple += period.multiple_candidates_count || 0;
          totalUncertain += period.uncertain_count || 0;
          totalClassifications += period.total_classifications || 0;
          totalPredictionTime += period.avg_prediction_time_ms || 0;
          periodCount++;
        });

        const avgTime = periodCount > 0 ? totalPredictionTime / periodCount : 0;

        setTotalClassifications(totalClassifications);
        setAvgPredictionTime(avgTime);

        const data = [
          { 
            name: t("highConfidence"), 
            count: totalHigh, 
            percentage: totalClassifications > 0 ? (totalHigh / totalClassifications) * 100 : 0,
            color: "var(--chart-1)"
          },
          { 
            name: t("lowConfidence"), 
            count: totalLow, 
            percentage: totalClassifications > 0 ? (totalLow / totalClassifications) * 100 : 0,
            color: "var(--chart-2)"
          },
          { 
            name: t("multipleCandidates"), 
            count: totalMultiple, 
            percentage: totalClassifications > 0 ? (totalMultiple / totalClassifications) * 100 : 0,
            color: "var(--chart-3)"
          },
          { 
            name: t("uncertain"), 
            count: totalUncertain, 
            percentage: totalClassifications > 0 ? (totalUncertain / totalClassifications) * 100 : 0,
            color: "var(--chart-4)"
          },
        ];

        setChartData(data);
      }
      // No data available
      else {
        setTotalClassifications(0);
        setAvgPredictionTime(0);
        setChartData([]);
      }
    } catch (err) {
      setError("Failed to fetch classification data");
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
      setChartLoading(false);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      );
    }

    if (error) {
      return (
        <Card>
          <CardContent className="flex items-center justify-center h-64">
            <p className="text-red-500">{error}</p>
          </CardContent>
        </Card>
      );
    }

    if (!chartData.length || totalClassifications === 0) {
      return (
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">{t("heading")}</h1>
            <p className="text-muted-foreground mt-2">{t("description")}</p>
          </div>
          
          <div className="flex gap-4">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder={t("selectModel")} />
            </SelectTrigger>
            <SelectContent>
              {availableModels.map((model) => (
                <SelectItem key={model.name} value={model.name}>
                  {model.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

            <Select value={selectedHours} onValueChange={setSelectedHours}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder={t("selectPeriod")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="24">{t("last24Hours")}</SelectItem>
                <SelectItem value="48">{t("last48Hours")}</SelectItem>
                <SelectItem value="72">{t("last72Hours")}</SelectItem>
                <SelectItem value="168">{t("lastWeek")}</SelectItem>
                <SelectItem value="336">{t("last2Weeks")}</SelectItem>
                <SelectItem value="720">{t("last30Days")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Card>
            <CardContent className="flex items-center justify-center h-64">
              <p className="text-muted-foreground">{t("noDataAvailable")}</p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">{t("heading")}</h1>
          <p className="text-muted-foreground mt-2">{t("description")}</p>
        </div>
        
        <div className="flex gap-4">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder={t("selectModel")} />
            </SelectTrigger>
            <SelectContent>
              {availableModels.map((model) => (
                <SelectItem key={model.name} value={model.name}>
                  {model.display_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedHours} onValueChange={setSelectedHours}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder={t("selectPeriod")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="24">{t("last24Hours")}</SelectItem>
              <SelectItem value="48">{t("last48Hours")}</SelectItem>
              <SelectItem value="72">{t("last72Hours")}</SelectItem>
              <SelectItem value="168">{t("lastWeek")}</SelectItem>
              <SelectItem value="336">{t("last2Weeks")}</SelectItem>
              <SelectItem value="720">{t("last30Days")}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Classification Confidence Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80 w-full transition-opacity duration-300">
              {chartLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-6 w-6 animate-spin" />
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
                      height={80}
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) =>
                        value && value.length > 12
                          ? `${value.substring(0, 12)}...`
                          : value
                      }
                    />
                    <YAxis />
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
                              <span className="text-muted-foreground">count</span>
                              <span className="text-foreground font-mono font-medium tabular-nums">
                                {data.value?.toLocaleString()}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-muted-foreground">percentage</span>
                              <span className="text-foreground font-mono font-medium tabular-nums">
                                {data.payload?.percentage?.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        );
                      }}
                    />
                    <Bar dataKey="count" radius={8}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ChartContainer>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex-col items-start gap-2 text-sm">
            <div className="flex gap-2 leading-none font-medium">
              <span>{t("totalClassifications")}: {totalClassifications.toLocaleString()}</span>
            </div>
            <div className="text-muted-foreground leading-none">
              {t("avgPredictionTime")}: {avgPredictionTime.toFixed(1)} ms
            </div>
          </CardFooter>
        </Card>
      </div>
    );
  };

  return (
    <ProtectedRoute>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator
                orientation="vertical"
                className="mr-2 data-[orientation=vertical]:h-4"
              />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/dashboard">
                      {getT("navigation.dashboard")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/ai-services">
                      {getT("navigation.ai_services")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <span className="font-medium">{t("heading")}</span>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
            <div className="container mx-auto p-6">
              {renderContent()}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
