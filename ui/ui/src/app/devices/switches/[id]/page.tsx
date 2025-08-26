"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { fetchNetworkDevice, fetchBridges } from "@/lib/devices";
import { toast } from "sonner";
import SwitchEditComponent from "@/components/devices/SwitchEditComponent";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { RingLoader } from "react-spinners";
import DeviceStatsGraph from "@/components/graphs/DeviceStatsGraph";
import PortStatsGraph from "@/components/graphs/PortStatsGraph";
import BridgeDataComponent from "@/components/devices/BridgeDataComponent";
import ConnectionIndicator from "@/components/devices/ConnectionIndicator";
import { useLanguage } from "@/context/languageContext";

import { BridgeApiResponse, NetworkDeviceDetails } from "@/lib/types";

export default function SwitchEditPage() {
  const { getT } = useLanguage();
  const { id } = useParams();
  const [switchData, setSwitchData] = useState<NetworkDeviceDetails | null>(
    null
  );
  const [isLoadingSwitchData, setIsLoadingSwitchData] = useState(true);
  const [bridgeData, setBridgeData] = useState<BridgeApiResponse | null>(null);
  const [isLoadingBridgeData, setIsLoadingBridgeData] = useState(true);

  const fetchData = useCallback(async () => {
    setIsLoadingSwitchData(true);
    setIsLoadingBridgeData(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken") || ""
          : "";

      // Fetch switch data and bridge data in parallel
      const [switchDataResult, bridgeDataResult] = await Promise.all([
        fetchNetworkDevice(token, id as string),
        fetchBridges(token, id as string),
      ]);

      setSwitchData(switchDataResult);
      setBridgeData(bridgeDataResult);
      setIsLoadingSwitchData(false);
      setIsLoadingBridgeData(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error(getT("page.SwitchesPage.fetch_error"));
      setIsLoadingSwitchData(false);
      setIsLoadingBridgeData(false);
    }
  }, [id, getT]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUpdate = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

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
                      {getT("navigation.network")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/devices/switches">
                      {getT("navigation.switches")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href={`/devices/switches/${id}`}>
                      {switchData?.name}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="flex flex-1 flex-col w-full items-center py-8">
            {isLoadingSwitchData || isLoadingBridgeData ? (
              <div className="w-full flex justify-center py-12">
                <RingLoader color="#7456FD" size={60} loading={true} />
              </div>
            ) : (
              <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8">
                <div className="flex items-center justify-between mb-4 w-full">
                  <h2 className="text-xl font-bold ml-4">
                    {switchData?.name} {getT("page.SwitchesPage.details")}
                  </h2>
                  <ConnectionIndicator
                    deviceIp={switchData?.lan_ip_address as string}
                    deviceType={switchData?.device_type as string}
                  />
                </div>
                <div className="grid grid-cols-1 @xl/main:grid-cols-1 gap-6">
                  <SwitchEditComponent
                    switchData={switchData as NetworkDeviceDetails}
                    onUpdate={handleUpdate}
                  />
                  <DeviceStatsGraph
                    switchId={id as string}
                    ipAddress={switchData?.lan_ip_address as string}
                  />
                  <BridgeDataComponent
                    fetchData={fetchData}
                    isLoading={isLoadingBridgeData}
                    bridgeData={bridgeData}
                    deviceIp={switchData?.lan_ip_address as string}
                  />
                  {bridgeData?.bridges &&
                    bridgeData.bridges.length > 0 &&
                    bridgeData.bridges[0].ports &&
                    bridgeData.bridges[0].ports.length > 0 && (
                      <PortStatsGraph
                        targetIpAddress={switchData?.lan_ip_address as string}
                        targetPorts={bridgeData.bridges[0].ports}
                      />
                    )}
                </div>
              </div>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
