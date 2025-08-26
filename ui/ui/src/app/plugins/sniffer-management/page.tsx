/*
 * File: page.tsx
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

import React, { useState, useEffect, useCallback } from "react";
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
import ProtectedRoute from "@/lib/ProtectedRoute";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";
import { SnifferInstallationList } from "@/components/plugins/SnifferInstallationList";
import { fetchInstalledPlugins } from "@/lib/software";
import { PluginInstallation } from "@/lib/types";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { usePluginContext } from "@/context/PluginContext";

export default function SnifferManagementPage() {
  const { getT } = useLanguage();
  const { token } = useAuth();
  const { loadInstalledPlugins } = usePluginContext();

  const [installedPlugins, setInstalledPlugins] = useState<
    PluginInstallation[]
  >([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    setError("");

    try {
      const installedPluginsData = await fetchInstalledPlugins(token);
      setInstalledPlugins(installedPluginsData);
    } catch (err) {
      console.error("Failed to load sniffer data:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load data.";
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    loadData(); // Refresh data
    loadInstalledPlugins(); // Refresh sidebar
  };

  if (isLoading) {
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
                      <BreadcrumbLink href="/plugins">
                        {getT("navigation.plugins", "Plugins")}
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                  </BreadcrumbList>
                </Breadcrumb>
              </div>
            </header>

            <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
              <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </ProtectedRoute>
    );
  }

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
                    <BreadcrumbLink href="/plugins">
                      {getT("navigation.plugins", "Plugins")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>

          <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
            <div className="w-full flex flex-row items-end justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-muted-foreground">
                  {getT(
                    "page.SnifferManagement.page_title",
                    "Sniffer Management"
                  )}
                </h1>
                <p className="text-muted-foreground mt-2">
                  {getT(
                    "page.SnifferManagement.page_description",
                    "Manage and configure traffic classification sniffers"
                  )}
                </p>
              </div>
            </div>

            {error && toast.error(error)}

            <SnifferInstallationList
              installations={installedPlugins}
              onRefresh={handleRefresh}
            />
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
