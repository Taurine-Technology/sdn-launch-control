"use client";

import React from "react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ProtectedRoute from "@/lib/ProtectedRoute";
import AggregatedClassificationGraph from "@/components/graphs/AggregatedClassificationGraph";
import RealTimeClassificationsGraph from "@/components/graphs/RealTimeClassificationsGraph";
import AggregatedDataUsePerUser from "@/components/graphs/AggregatedDataUsePerUser";
import MacAddressClassificationGraph from "@/components/graphs/MacAddressClassificationGraph";
import UserDataUsageGraph from "@/components/graphs/UserDataUsageGraph";
import DataPerClassification from "@/components/graphs/DataPerClassification";
import { useLanguage } from "@/context/languageContext";

export default function ClassificationsPage() {
  const { getT } = useLanguage();

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
                    <BreadcrumbLink href="/monitoring/classifications">
                      {getT("navigation.monitoring", "Monitoring")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/monitoring/classifications">
                      {getT(
                        "page.MonitoringPage.classifications",
                        "Classifications"
                      )}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            <h1 className="text-2xl font-bold">
              {getT(
                "page.MonitoringPage.classification_graphs",
                "Classification Graphs"
              )}
            </h1>

            <Tabs defaultValue="realtime" className="w-full">
              <div className="w-full overflow-hidden">
                <TabsList className="flex w-full overflow-x-auto gap-1 tabs-scrollbar">
                  <TabsTrigger
                    value="realtime"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT(
                      "page.RealTimeClassificationsGraph.title",
                      "Real-time Classifications"
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="aggregated"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT(
                      "page.AggregatedClassificationGraph.title",
                      "Aggregated Classification"
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="data-usage"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT(
                      "page.AggregatedDataUsePerUser.title",
                      "Data Usage Per User"
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="device-classification"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT(
                      "page.MacAddressClassificationGraph.title",
                      "Device Classification"
                    )}
                  </TabsTrigger>
                  <TabsTrigger
                    value="user-data-usage"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT("page.UserDataUsageGraph.title", "User Data Usage")}
                  </TabsTrigger>
                  <TabsTrigger
                    value="data-per-classification"
                    className="flex-shrink-0 whitespace-nowrap min-w-fit"
                  >
                    {getT(
                      "page.DataPerClassificationGraph.title",
                      "Data Per Classification"
                    )}
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value="realtime" className="space-y-4">
                <RealTimeClassificationsGraph />
              </TabsContent>

              <TabsContent value="aggregated" className="space-y-4">
                <AggregatedClassificationGraph />
              </TabsContent>

              <TabsContent
                value="data-usage"
                className="space-y-4 lg:max-h-[300px]"
              >
                <AggregatedDataUsePerUser />
              </TabsContent>

              <TabsContent value="device-classification" className="space-y-4">
                <MacAddressClassificationGraph />
              </TabsContent>

              <TabsContent value="user-data-usage" className="space-y-4">
                <UserDataUsageGraph />
              </TabsContent>

              <TabsContent
                value="data-per-classification"
                className="space-y-4"
              >
                <DataPerClassification />
              </TabsContent>
            </Tabs>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
