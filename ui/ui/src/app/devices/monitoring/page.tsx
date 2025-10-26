"use client";

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { 
  Activity, 
  AlertTriangle, 
  Monitor
} from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";
import { 
  fetchDeviceUptimeStatus, 
  toggleDeviceMonitoring
} from "@/lib/deviceMonitoring";
import { createAxiosInstanceWithToken } from "@/lib/axiosInstance";
import { DeviceUptimeStatus } from "@/lib/types";
import RingLoader from "react-spinners/RingLoader";
import DeviceUptimeOverview from "@/components/devices/DeviceUptimeOverview";
import DeviceUptimeCharts from "@/components/devices/DeviceUptimeCharts";
import DeviceManagementTable from "@/components/devices/DeviceManagementTable";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";

export default function DeviceMonitoringPage() {
  const { getT } = useLanguage();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = React.useState("overview");
  const [uptimeStatus, setUptimeStatus] = React.useState<DeviceUptimeStatus[]>([]);
  const [totalDevices, setTotalDevices] = React.useState(0);
  const [monitoredDevices, setMonitoredDevices] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadUptimeStatus = React.useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    setError(null);
    try {
      // Fetch all network devices for accurate counts
      const axiosInstance = createAxiosInstanceWithToken(token);
      const { data: allDevicesResponse } = await axiosInstance.get("/network-devices/?page_size=200");
      const allDevices = allDevicesResponse.results || allDevicesResponse;
      
      setTotalDevices(allDevices.length);
      setMonitoredDevices(allDevices.filter((d: { is_ping_target: boolean }) => d.is_ping_target).length);
      
      // Fetch uptime status for devices that have been pinged
      const status = await fetchDeviceUptimeStatus(token, "24 hours");
      setUptimeStatus(status);
    } catch (err) {
      console.error("Error loading uptime status:", err);
      setError("Failed to load device monitoring data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  React.useEffect(() => {
    loadUptimeStatus();
  }, [loadUptimeStatus]);

  const handleToggleMonitoring = async (deviceId: number, enable: boolean) => {
    if (!token) return;
    
    try {
      await toggleDeviceMonitoring(token, {
        device_id: deviceId,
        is_ping_target: enable
      });
      // Reload data after toggle
      await loadUptimeStatus();
    } catch (err) {
      console.error("Error toggling monitoring:", err);
      setError("Failed to update monitoring status");
    }
  };


  const t = React.useCallback((key: string) => getT(`deviceMonitoring.${key}`), [getT]);

  if (loading && uptimeStatus.length === 0) {
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
                    <BreadcrumbLink asChild>
                      <Link href="/dashboard">
                        {getT("navigation.dashboard", "Dashboard")}
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink asChild>
                      <Link href="/devices/monitoring">
                        {getT("navigation.device_monitoring", "Device Monitoring")}
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="flex items-center justify-center min-h-[400px]">
            <RingLoader color="var(--color-logo-orange)" size={48} />
          </div>
        </SidebarInset>
      </SidebarProvider>
    );
  }

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
                  <BreadcrumbLink asChild>
                    <Link href="/dashboard">
                      {getT("navigation.dashboard", "Dashboard")}
                    </Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
                <BreadcrumbItem>
                  <BreadcrumbLink asChild>
                    <Link href="/devices/monitoring">
                      {getT("navigation.device_monitoring", "Device Monitoring")}
                    </Link>
                  </BreadcrumbLink>
                </BreadcrumbItem>
              </BreadcrumbList>
            </Breadcrumb>
          </div>
        </header>
        <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
          <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t("title")}</h1>
          <p className="text-muted-foreground">{t("description")}</p>
        </div>
        <Button onClick={loadUptimeStatus} disabled={loading}>
          {loading ? (
            <RingLoader color="white" size={16} />
          ) : (
            <Activity className="h-4 w-4 mr-2" />
          )}
          {t("refresh")}
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-800">
              <AlertTriangle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t("totalDevices")}</CardTitle>
            <Monitor className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalDevices}</div>
            <p className="text-xs text-muted-foreground">{t("devicesTracked")}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{t("monitoredDevices")}</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {monitoredDevices}
            </div>
            <p className="text-xs text-muted-foreground">{t("activeMonitoring")}</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Section */}
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Monitoring Views</h2>
          <p className="text-sm text-muted-foreground">
            View device uptime data in different formats and manage monitoring settings
          </p>
        </div>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">{t("overviewTab")}</TabsTrigger>
            <TabsTrigger value="charts">{t("chartsTab")}</TabsTrigger>
            <TabsTrigger value="management">{t("managementTab")}</TabsTrigger>
          </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <DeviceUptimeOverview />
        </TabsContent>

        <TabsContent value="charts" className="space-y-4">
          <DeviceUptimeCharts />
        </TabsContent>

        <TabsContent value="management" className="space-y-4">
          <DeviceManagementTable 
            onToggleMonitoring={handleToggleMonitoring}
          />
        </TabsContent>
        </Tabs>
      </div>
    </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
