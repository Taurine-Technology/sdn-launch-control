"use client";

import { useParams } from "next/navigation";

import { useEffect, useState, useCallback } from "react";
import { Controller } from "@/lib/types";
import { fetchController } from "@/lib/devices";
import { toast } from "sonner";
import ProtectedRoute from "@/lib/ProtectedRoute";
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
import { RingLoader } from "react-spinners";
import ConnectionIndicator from "@/components/devices/ConnectionIndicator";
import ControllerEditComponent from "@/components/devices/ControllerEditComponent";
import { useLanguage } from "@/context/languageContext";

export default function ControllerEditPage() {
  const { getT } = useLanguage();
  const { id } = useParams();

  const [controller, setController] = useState<Controller | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken") || ""
          : "";
      const controller = await fetchController(token, id as string);
      setController(controller);
    } catch (error) {
      console.error("[ControllerEditPage] Error fetching controller", error);
      toast.error(
        getT(
          "components.devices.controller_edit.error",
          "Error fetching controller"
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [id, getT]);

  useEffect(() => {
    setIsLoading(true);
    fetchData();
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
                      {getT("navigation.dashboard", "Dashboard")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/devices/controllers">
                      {getT("navigation.controllers", "Controllers")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href={`/devices/controllers/${id}`}>
                      {controller?.lan_ip_address}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="flex flex-1 flex-col w-full items-center py-8">
            {isLoading ? (
              <div className="w-full flex justify-center py-12">
                <RingLoader color="#7456FD" size={60} loading={true} />
              </div>
            ) : (
              <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8">
                <div className="flex items-center justify-between mb-4 w-full">
                  <h2 className="text-xl font-bold ml-4">
                    {getT(
                      "components.devices.controller_edit.title",
                      "Controller"
                    )}{" "}
                    @ {controller?.lan_ip_address}
                  </h2>
                  <ConnectionIndicator
                    deviceIp={controller?.lan_ip_address as string}
                    deviceType="controller"
                  />
                </div>
                <div className="grid grid-cols-1 @xl/main:grid-cols-1 gap-6">
                  <ControllerEditComponent
                    controllerData={controller as Controller}
                    onUpdate={fetchData}
                  />
                </div>
              </div>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
