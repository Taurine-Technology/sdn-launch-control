"use client";

import { useState } from "react";
import NetworkDiagramComponent from "@/components/network/NetworkDiagramComponent";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLanguage } from "@/context/languageContext";
import NetworkThroughputChart from "@/components/dashboard/NetworkThroughputChart";
import UserActivityChart from "@/components/dashboard/UserActivityChart";
import DashboardDeviceStats from "@/components/dashboard/DashboardDeviceStats";

type TimeRange = "5min" | "1hour" | "24hour" | "7days";

export default function Dashboard() {
  const { getT } = useLanguage();
  const [timeRange, setTimeRange] = useState<TimeRange>("1hour");

  return (
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
                    {getT("navigation.dashboard", "Dashboard")}
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Network Overview</h2>
            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Time Range:</label>
              <Select value={timeRange} onValueChange={(value) => setTimeRange(value as TimeRange)}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5min">5 Minutes</SelectItem>
                  <SelectItem value="1hour">1 Hour</SelectItem>
                  <SelectItem value="24hour">24 Hours</SelectItem>
                  <SelectItem value="7days">7 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <NetworkThroughputChart timeRange={timeRange} />
            <UserActivityChart timeRange={timeRange} />
            <div className="md:col-span-2">
              <DashboardDeviceStats />
            </div>
          </div>
          <NetworkDiagramComponent />
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
