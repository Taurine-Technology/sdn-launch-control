"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Bell } from "lucide-react";
import { useRouter } from "next/navigation";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCcw, Check } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  listNetworkNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/networkNotifications";
import type { NetworkNotification, PaginatedResponse } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

type TabKey = "unread" | "read" | "all";

export function NotificationPanel() {
  const router = useRouter();
  const { getT } = useLanguage();
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("unread");
  const [data, setData] =
    useState<PaginatedResponse<NetworkNotification> | null>(null);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<string>("");
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const readFilter = useMemo(() => {
    if (activeTab === "unread") return "false" as const;
    if (activeTab === "read") return "true" as const;
    return undefined;
  }, [activeTab]);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const resp = await listNetworkNotifications(token, {
        page: 1,
        page_size: 20,
        read: readFilter,
      });
      setData(resp);
      // Update unread count independently
      const unreadResp = await listNetworkNotifications(token, {
        page: 1,
        page_size: 1,
        read: "false",
      });
      setUnreadCount(unreadResp.count || 0);
    } finally {
      setLoading(false);
    }
  }, [token, readFilter]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setToken(localStorage.getItem("taurineToken") || "");
    }
  }, []);

  // Fetch unread count once on page load (and whenever token becomes available)
  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const unreadResp = await listNetworkNotifications(token, {
          page: 1,
          page_size: 1,
          read: "false",
        });
        setUnreadCount(unreadResp.count || 0);
      } catch {
        // ignore
      }
    })();
  }, [token]);

  // Background polling every 30s: update unread count, and if open, refresh list
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(async () => {
      try {
        const unreadResp = await listNetworkNotifications(token, {
          page: 1,
          page_size: 1,
          read: "false",
        });
        setUnreadCount(unreadResp.count || 0);
        if (open) {
          await refresh();
        }
      } catch {
        // ignore polling errors
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [token, open, refresh]);

  useEffect(() => {
    if (open) refresh();
  }, [open, activeTab, token, refresh]);

  const openNotification = async (n: NetworkNotification) => {
    try {
      if (!n.read) await markNotificationRead(token, n.id);
    } catch {
      // ignore
    }
    setOpen(false);
    router.push(`/network-notifications/${n.id}`);
  };

  const onMarkRead = async (n: NetworkNotification) => {
    await markNotificationRead(token, n.id);
    refresh();
  };

  const onMarkAllRead = async () => {
    await markAllNotificationsRead(token);
    refresh();
  };

  const formatTime = (iso?: string | null) => {
    if (!iso) return "";
    const d = new Date(iso);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const sec = Math.floor(diffMs / 1000);
    const min = Math.floor(sec / 60);
    const hr = Math.floor(min / 60);
    if (sec < 45)
      return getT(
        "components.notifications.notification_panel.just_now",
        "Just now"
      );
    if (min < 60)
      return getT(
        "components.notifications.notification_panel.minutes_ago",
        "{minutes}m ago"
      ).replace("{minutes}", String(min));
    if (hr < 24)
      return getT(
        "components.notifications.notification_panel.hours_ago",
        "{hours}h ago"
      ).replace("{hours}", String(hr));
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (
      d.getFullYear() === yesterday.getFullYear() &&
      d.getMonth() === yesterday.getMonth() &&
      d.getDate() === yesterday.getDate()
    )
      return getT(
        "components.notifications.notification_panel.yesterday",
        "Yesterday"
      );
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={getT(
            "components.notifications.notification_panel.notifications_title",
            "Notifications"
          )}
          className="relative"
        >
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-5 h-5 px-1 rounded-full bg-primary text-primary-foreground text-[10px] leading-5 text-center">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-96 p-0">
        {/* A11y title for Radix Dialog base */}
        <SheetHeader className="sr-only">
          <SheetTitle>
            {getT(
              "components.notifications.notification_panel.notifications_title",
              "Notifications"
            )}
          </SheetTitle>
        </SheetHeader>
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between pr-12">
            <Tabs
              value={activeTab}
              onValueChange={(v) => setActiveTab(v as TabKey)}
            >
              <TabsList>
                <TabsTrigger value="unread">
                  {getT(
                    "components.notifications.notification_panel.tab_unread",
                    "Unread"
                  )}
                </TabsTrigger>
                <TabsTrigger value="read">
                  {getT(
                    "components.notifications.notification_panel.tab_read",
                    "Read"
                  )}
                </TabsTrigger>
                <TabsTrigger value="all">
                  {getT(
                    "components.notifications.notification_panel.tab_all",
                    "All"
                  )}
                </TabsTrigger>
              </TabsList>
            </Tabs>
            <Button
              className="mr-2"
              variant="ghost"
              size="icon"
              aria-label={getT(
                "components.notifications.notification_panel.refresh",
                "Refresh"
              )}
              onClick={refresh}
              disabled={loading}
            >
              <RefreshCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <ScrollArea className="h-[calc(100%-112px)]">
          <div className="divide-y divide-border">
            {(data?.results || []).map((n) => (
              <Card key={n.id} className="rounded-none shadow-none border-0">
                <CardContent className="p-4 border-b last:border-b-0">
                  <div className="flex items-start justify-between gap-3">
                    <div
                      className="flex-1 cursor-pointer"
                      onClick={() => openNotification(n)}
                    >
                      <p className="font-medium flex items-center gap-2">
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
                        {!n.read && (
                          <span className="ml-1 inline-block h-2 w-2 rounded-full bg-primary align-middle" />
                        )}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {n.description}
                      </p>
                      <span className="text-[11px] text-muted-foreground">
                        {formatTime(n.created_at)}
                      </span>
                    </div>
                    {!n.read && (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={getT(
                          "components.notifications.notification_panel.mark_as_read",
                          "Mark as read"
                        )}
                        onClick={() => onMarkRead(n)}
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {!loading && data && data.count === 0 && (
              <div className="p-4 text-sm text-muted-foreground">
                {getT(
                  "components.notifications.notification_panel.no_notifications",
                  "No notifications."
                )}
              </div>
            )}
            {loading && (
              <div className="p-4 text-sm text-muted-foreground">
                {getT(
                  "components.notifications.notification_panel.loading",
                  "Loading..."
                )}
              </div>
            )}
          </div>
        </ScrollArea>
        <div className="px-4 py-2 border-t flex items-center justify-between text-xs text-muted-foreground">
          <div>
            {getT(
              "components.notifications.notification_panel.view_all_in",
              "View all in"
            )}{" "}
            <button
              className="underline"
              onClick={() => {
                setOpen(false);
                router.push("/network-notifications");
              }}
            >
              {getT(
                "components.notifications.notification_panel.network_notifications",
                "Network Notifications"
              )}
            </button>
          </div>
          <Button variant="secondary" size="sm" onClick={onMarkAllRead}>
            {getT(
              "components.notifications.notification_panel.mark_all_read",
              "Mark all as read"
            )}
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
