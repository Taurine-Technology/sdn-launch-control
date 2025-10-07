"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
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
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import ProtectedRoute from "@/lib/ProtectedRoute";
import {
  getNetworkNotification,
  markNotificationRead,
} from "@/lib/networkNotifications";
import type { NetworkNotification } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

/**
 * Renders the detail page for a single network notification, fetching the notification by ID, marking it read if necessary, and displaying its details.
 *
 * @returns The rendered Network Notification detail page as a JSX element
 */
export default function NetworkNotificationDetailPage() {
  const params = useParams<{ id: string }>();
  const { getT } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState<NetworkNotification | null>(
    null
  );
  const [token, setToken] = useState("");

  const id = Number(params.id);

  useEffect(() => {
    setToken(localStorage.getItem("taurineToken") || "");
  }, []);

  const fetchData = useCallback(async () => {
    if (!token || Number.isNaN(id)) return;
    setLoading(true);
    try {
      const { notification } = await getNetworkNotification(token, id);
      setNotification(notification);
      if (!notification.read) {
        await markNotificationRead(token, id);
        setNotification({ ...notification, read: true });
      }
    } finally {
      setLoading(false);
    }
  }, [token, id]);

  useEffect(() => {
    if (token) {
      fetchData();
    }
  }, [id, token, fetchData]);

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
                    <BreadcrumbLink href="/network-notifications">
                      {getT(
                        "navigation.network_notifications",
                        "Network Notifications"
                      )}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="#">
                      {getT(
                        "page.NetworkNotificationDetailPage.notification_number",
                        `Notification #${id}`
                      ).replace("{id}", String(id))}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>

          <div className="@container/main w-full max-w-4xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            {loading && (
              <div className="flex flex-col gap-3">
                <Skeleton className="h-10 w-1/3" />
                <Skeleton className="h-24 w-full" />
              </div>
            )}

            {!loading && notification && (
              <Card>
                <CardHeader>
                  <CardTitle>
                    <span>{notification.type}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    {getT("page.NetworkNotificationDetailPage.id_label", "ID")}:{" "}
                    {notification.id}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {getT(
                      "page.NetworkNotificationDetailPage.status_label",
                      "Status"
                    )}
                    :{" "}
                    {notification.read
                      ? getT(
                          "page.NetworkNotificationDetailPage.status_read",
                          "Read"
                        )
                      : getT(
                          "page.NetworkNotificationDetailPage.status_unread",
                          "Unread"
                        )}
                  </div>
                  <Separator />
                  <div className="whitespace-pre-wrap leading-relaxed">
                    {notification.description}
                  </div>
                  {notification.user && (
                    <div className="text-sm text-muted-foreground">
                      {getT(
                        "page.NetworkNotificationDetailPage.user_label",
                        "User"
                      )}
                      : {notification.user}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {!loading && !notification && (
              <div className="text-muted-foreground">
                {getT(
                  "page.NetworkNotificationDetailPage.not_found",
                  "Notification not found."
                )}
              </div>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}