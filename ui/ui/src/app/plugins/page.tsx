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
import { PluginCard } from "@/components/plugins/PluginCard";
import { fetchPlugins, fetchInstalledPlugins } from "@/lib/software";
import { Plugin, PluginInstallation, NetworkDeviceDetails } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Loader2, Search } from "lucide-react";
import { toast } from "sonner";
import { fetchSwitches } from "@/lib/devices";
import { usePluginContext } from "@/context/PluginContext";

export default function PluginsPage() {
  const { getT } = useLanguage();
  const { token } = useAuth();
  const { loadInstalledPlugins } = usePluginContext();

  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [installedPlugins, setInstalledPlugins] = useState<
    PluginInstallation[]
  >([]);
  const [devices, setDevices] = useState<NetworkDeviceDetails[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const loadData = useCallback(async () => {
    if (!token) return;

    setIsLoading(true);
    setError("");

    try {
      const [pluginsData, installedPluginsData, devicesData] =
        await Promise.all([
          fetchPlugins(token),
          fetchInstalledPlugins(token),
          fetchSwitches(token),
        ]);

      setPlugins(pluginsData);
      setInstalledPlugins(installedPluginsData);
      setDevices(devicesData as NetworkDeviceDetails[]);
    } catch (err) {
      console.error("Failed to load plugin data:", err);
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

  const handleInstallSuccess = () => {
    loadData(); // Refresh data after successful installation
    loadInstalledPlugins(); // Refresh sidebar
  };

  const handleUninstallSuccess = () => {
    loadData(); // Refresh data after successful uninstallation
    loadInstalledPlugins(); // Refresh sidebar
  };

  // Create a map of installed plugins for quick lookup
  const installedPluginMap = new Map(
    installedPlugins.map((installation) => [
      installation.plugin.id,
      installation,
    ])
  );

  // Filter plugins based on search query
  const filteredPlugins = plugins.filter((plugin) => {
    return (
      plugin.alias.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plugin.short_description.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const getInstallationForPlugin = (pluginId: number) => {
    return installedPluginMap.get(pluginId);
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
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin" />
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
              <h1 className="text-2xl font-bold text-muted-foreground">
                {getT("page.PluginsPage.page_title", "Plugins")}
              </h1>
            </div>

            {error && toast.error(error)}

            <div className="flex flex-col gap-6">
              <div className="relative max-w-sm">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder={getT("page.PluginsPage.search_placeholder")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredPlugins.map((plugin) => (
                  <PluginCard
                    key={plugin.id}
                    plugin={plugin}
                    installation={getInstallationForPlugin(plugin.id)}
                    devices={devices}
                    installations={installedPlugins}
                    onInstallSuccess={handleInstallSuccess}
                    onUninstallSuccess={handleUninstallSuccess}
                  />
                ))}
              </div>

              {filteredPlugins.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">
                    {searchQuery
                      ? getT("page.PluginsPage.no_plugins_search")
                      : getT("page.PluginsPage.no_plugins_available")}
                  </p>
                </div>
              )}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
