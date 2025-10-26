"use client";
import React, { useEffect, useState } from "react";

import { NetworkDeviceDetails } from "@/lib/types";
import { DeviceOverviewTable } from "@/components/network/DeviceOverviewTable";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import Link from "next/link";
import { Separator } from "@/components/ui/separator";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { createAxiosInstanceWithToken } from "@/lib/axiosInstance"; // TODO: change the call to external devices.ts file
import { useLanguage } from "@/context/languageContext";

export default function DevicesOverviewPage() {
  const { getT } = useLanguage();
  const [devices, setDevices] = useState<NetworkDeviceDetails[]>([]);
  const [count, setCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterVerified, setFilterVerified] = useState("all");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const DEVICE_TYPE_OPTIONS = [
    {
      value: "all",
      label: getT("page.DevicesOverviewPage.all_types", "All Types"),
    },
    {
      value: "switch",
      label: getT("page.DevicesOverviewPage.switch", "Switch"),
    },
    {
      value: "access_point",
      label: getT("page.DevicesOverviewPage.access_point", "Access Point"),
    },
    {
      value: "server",
      label: getT("page.DevicesOverviewPage.server", "Server"),
    },
    {
      value: "controller",
      label: getT("page.DevicesOverviewPage.controller", "Controller"),
    },
    { value: "vm", label: getT("page.DevicesOverviewPage.vm", "VM") },
    {
      value: "end_user",
      label: getT("page.DevicesOverviewPage.end_user", "End User"),
    },
  ];
  const VERIFIED_OPTIONS = [
    { value: "all", label: getT("page.DevicesOverviewPage.all", "All") },
    {
      value: "true",
      label: getT("page.DevicesOverviewPage.verified", "Verified"),
    },
    {
      value: "false",
      label: getT("page.DevicesOverviewPage.not_verified", "Not Verified"),
    },
  ];

  // Updated setters to reset page to 1
  const handleSetSearch = (v: string) => {
    setSearch(v);
    setPage(1);
  };
  const handleSetFilterType = (v: string) => {
    setFilterType(v);
    setPage(1);
  };
  const handleSetFilterVerified = (v: string) => {
    setFilterVerified(v);
    setPage(1);
  };

  const getDevices = async () => {
    setIsLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("taurineToken") || "";
      const params: string[] = [];
      if (search) params.push(`search=${encodeURIComponent(search)}`);
      if (filterType && filterType !== "all")
        params.push(`device_type=${encodeURIComponent(filterType)}`);
      if (filterVerified && filterVerified !== "all")
        params.push(`verified=${filterVerified}`);
      params.push(`page=${page}`);
      params.push(`page_size=${pageSize}`);
      const query = params.length ? `?${params.join("&")}` : "";
      const axiosInstance = createAxiosInstanceWithToken(token);
      const { data } = await axiosInstance.get(`/network-devices/${query}`);
      setDevices(data.results || data);
      setCount(
        data.count || (data.results ? data.results.length : data.length)
      );
    } catch (err) {
      console.error("[DEVICES OVERVIEW PAGE] Error fetching devices.", err);
      setError(getT("page.DevicesOverviewPage.error_fetching"));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    getDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, filterType, filterVerified, page, pageSize]);

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
                    <BreadcrumbLink asChild>
                      <Link href="/dashboard">
                        {getT("navigation.dashboard", "Dashboard")}
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink asChild>
                      <Link href="/devices/overview">
                        {getT(
                          "page.DevicesOverviewPage.page_title",
                          "Devices Overview"
                        )}
                      </Link>
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            {/* If you have multiple sections, use grid here */}
            <DeviceOverviewTable
              devices={devices}
              count={count}
              isLoading={isLoading}
              error={error}
              search={search}
              setSearch={handleSetSearch}
              filterType={filterType}
              setFilterType={handleSetFilterType}
              filterVerified={filterVerified}
              setFilterVerified={handleSetFilterVerified}
              page={page}
              setPage={setPage}
              pageSize={pageSize}
              setPageSize={setPageSize}
              deviceTypeOptions={DEVICE_TYPE_OPTIONS}
              verifiedOptions={VERIFIED_OPTIONS}
              onDeviceUpdated={getDevices}
            />
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
