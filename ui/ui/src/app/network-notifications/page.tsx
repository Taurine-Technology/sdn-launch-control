"use client";

import React, { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Check } from "lucide-react";
import {
  listNetworkNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/networkNotifications";
import type { NetworkNotification, PaginatedResponse } from "@/lib/types";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { useLanguage } from "@/context/languageContext";

type TabKey = "unread" | "read" | "all";

const PAGE_SIZE_DEFAULT = 10;

/**
 * Render the Network Notifications page content with tabbed filtering, pagination, and per-notification actions.
 *
 * Synchronizes the active tab and page with the URL, loads an auth token from localStorage to fetch paginated notifications,
 * and exposes handlers to open notifications, mark individual notifications as read, and mark all as read.
 *
 * @returns The component's React element that displays the network notifications UI.
 */
function NetworkNotificationsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { getT } = useLanguage();
  const [activeTab, setActiveTab] = useState<TabKey>("unread");
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(PAGE_SIZE_DEFAULT);
  const [loading, setLoading] = useState<boolean>(true);
  const [data, setData] =
    useState<PaginatedResponse<NetworkNotification> | null>(null);
  const [token, setToken] = useState<string>("");

  const readFilter = useMemo(() => {
    if (activeTab === "unread") return "false" as const;
    if (activeTab === "read") return "true" as const;
    return undefined;
  }, [activeTab]);

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await listNetworkNotifications(token, {
        page,
        page_size: pageSize,
        read: readFilter,
      });
      setData(resp);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initialize from URL if present
    const tab = searchParams.get("tab") as TabKey | null;
    const p = Number(searchParams.get("page") || 1);
    if (tab && ["unread", "read", "all"].includes(tab)) setActiveTab(tab);
    if (!Number.isNaN(p)) setPage(p);
  }, [searchParams]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setToken(localStorage.getItem("taurineToken") || "");
    }
  }, []);

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, page, pageSize, token]);

  const updateUrl = (tab: TabKey, p: number) => {
    const qs = new URLSearchParams();
    qs.set("tab", tab);
    qs.set("page", String(p));
    router.replace(`/network-notifications?${qs.toString()}`);
  };

  const onTabChange = (val: string) => {
    const tab = (val as TabKey) || "unread";
    setActiveTab(tab);
    setPage(1);
    updateUrl(tab, 1);
  };

  const onOpenNotification = async (n: NetworkNotification) => {
    try {
      if (!n.read) await markNotificationRead(token, n.id);
    } catch {
      // ignore
    }
    router.push(`/network-notifications/${n.id}`);
  };

  const onMarkRead = async (n: NetworkNotification) => {
    await markNotificationRead(token, n.id);
    fetchData();
  };

  const onMarkAllRead = async () => {
    await markAllNotificationsRead(token);
    fetchData();
  };

  const pageCount = useMemo(() => {
    if (!data) return 1;
    return Math.max(1, Math.ceil(data.count / pageSize));
  }, [data, pageSize]);

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
                    <BreadcrumbLink href="#">
                      {getT("navigation.network", "Network")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/network-notifications">
                      {getT(
                        "navigation.network_notifications",
                        "Network Notifications"
                      )}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>

          <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold text-muted-foreground">
                {getT(
                  "page.NetworkNotificationsPage.page_title",
                  "Network Notifications"
                )}
              </h1>
              <Button variant="secondary" onClick={onMarkAllRead}>
                {getT(
                  "page.NetworkNotificationsPage.mark_all_read",
                  "Mark all as read"
                )}
              </Button>
            </div>

            <Tabs
              value={activeTab}
              onValueChange={onTabChange}
              className="flex flex-col min-h-[60vh]"
            >
              <div className="w-auto">
                <TabsList className="justify-start">
                  <TabsTrigger value="unread">
                    {getT("page.NetworkNotificationsPage.tab_unread", "Unread")}
                  </TabsTrigger>
                  <TabsTrigger value="read">
                    {getT("page.NetworkNotificationsPage.tab_read", "Read")}
                  </TabsTrigger>
                  <TabsTrigger value="all">
                    {getT("page.NetworkNotificationsPage.tab_all", "All")}
                  </TabsTrigger>
                </TabsList>
              </div>

              <TabsContent value={activeTab} className="flex flex-col flex-1">
                {loading && (
                  <div className="flex flex-1 items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                )}
                {!loading && (
                  <div className="flex flex-col gap-3">
                    {(data?.results || []).map((n) => (
                      <Card key={n.id} className={n.read ? "opacity-70" : ""}>
                        <CardContent className="p-4 flex items-center justify-between gap-4">
                          <div
                            className="flex-1 cursor-pointer"
                            onClick={() => onOpenNotification(n)}
                          >
                            <div className="text-sm text-muted-foreground flex items-center gap-2">
                              <span>{n.type}</span>
                              {n.urgency && (
                                <span
                                  className={
                                    `inline-flex items-center px-1.5 h-5 rounded text-[10px] ` +
                                    (n.urgency === "high"
                                      ? "bg-red-500 text-white"
                                      : n.urgency === "medium"
                                      ? "bg-amber-500 text-white"
                                      : "bg-emerald-500 text-white")
                                  }
                                >
                                  {n.urgency}
                                </span>
                              )}
                            </div>
                            <div className="font-medium">{n.description}</div>
                            <div className="text-[11px] text-muted-foreground mt-1">
                              {new Date(n.created_at || "").toLocaleString()}
                            </div>
                          </div>
                          {!n.read && (
                            <Button
                              variant="ghost"
                              size="icon"
                              aria-label={getT(
                                "page.NetworkNotificationsPage.mark_as_read",
                                "Mark as read"
                              )}
                              onClick={() => onMarkRead(n)}
                            >
                              <Check className="h-4 w-4" />
                            </Button>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                    {data && data.count === 0 && (
                      <div className="text-muted-foreground">
                        {getT(
                          "page.NetworkNotificationsPage.no_notifications",
                          "No notifications."
                        )}
                      </div>
                    )}
                  </div>
                )}

                <div className="mt-auto flex items-center justify-end gap-2 pt-4">
                  <Button
                    variant="outline"
                    disabled={page <= 1}
                    onClick={() => {
                      const p = Math.max(1, page - 1);
                      setPage(p);
                      updateUrl(activeTab, p);
                    }}
                  >
                    {getT("common.previous", "Previous")}
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    {getT(
                      "page.NetworkNotificationsPage.page_info",
                      "Page {page} of {pageCount}"
                    )
                      .replace("{page}", String(page))
                      .replace("{pageCount}", String(pageCount))}
                  </div>
                  <Button
                    variant="outline"
                    disabled={page >= pageCount}
                    onClick={() => {
                      const p = Math.min(pageCount, page + 1);
                      setPage(p);
                      updateUrl(activeTab, p);
                    }}
                  >
                    {getT("common.next", "Next")}
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
/**
 * Renders the Network Notifications page wrapped in a Suspense boundary with a localized loading fallback.
 *
 * @returns A React element containing the NetworkNotificationsContent component inside a Suspense wrapper
 */
export default function NetworkNotificationsPage() {
  const { getT } = useLanguage();
  return (
    <Suspense
      fallback={
        <div className="p-4 text-sm text-muted-foreground">
          {getT("page.NetworkNotificationsPage.loading_fallback", "Loading...")}
        </div>
      }
    >
      <NetworkNotificationsContent />
    </Suspense>
  );
}