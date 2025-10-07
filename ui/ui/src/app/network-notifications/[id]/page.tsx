"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { getNetworkNotification, markNotificationRead } from "@/lib/networkNotifications";
import type { NetworkNotification } from "@/lib/types";

/**
 * Page component that displays details for a single network notification and updates its read status.
 *
 * The component reads the notification `id` from route parameters, retrieves an auth token from
 * localStorage, fetches the notification data, and marks the notification as read if it was unread.
 * While fetching it shows skeleton placeholders; when data is available it renders the notification
 * details (type, id, read status, description, and user if present). The page is wrapped in access
 * control and a sidebar layout and includes a Back button that navigates to the previous route.
 *
 * @returns The React element for the network notification detail page.
 */
export default function NetworkNotificationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState<NetworkNotification | null>(
    null
  );
  const token = useMemo(() => localStorage.getItem("taurineToken") || "", []);

  const id = Number(params.id);

  const fetchData = async () => {
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
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <ProtectedRoute>
      <SidebarProvider
        style={{
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties}
      >
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/network-notifications">Network Notifications</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="#">Notification #{id}</BreadcrumbLink>
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
                  <CardTitle className="flex items-center justify-between">
                    <span>{notification.type}</span>
                    <Button variant="outline" onClick={() => router.back()}>
                      Back
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-sm text-muted-foreground">ID: {notification.id}</div>
                  <div className="text-sm text-muted-foreground">Status: {notification.read ? "Read" : "Unread"}</div>
                  <Separator />
                  <div className="whitespace-pre-wrap leading-relaxed">{notification.description}</div>
                  {notification.user && (
                    <div className="text-sm text-muted-foreground">User: {notification.user}</div>
                  )}
                </CardContent>
              </Card>
            )}

            {!loading && !notification && (
              <div className="text-muted-foreground">Notification not found.</div>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}

