"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Bell } from "lucide-react";
import { useRouter } from "next/navigation";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCcw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  listNetworkNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from "@/lib/networkNotifications";
import type { NetworkNotification, PaginatedResponse } from "@/lib/types";

type TabKey = "unread" | "read" | "all";

export function NotificationPanel() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<TabKey>("unread");
  const [data, setData] = useState<PaginatedResponse<NetworkNotification> | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<string>("");
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const readFilter = useMemo(() => {
    if (activeTab === "unread") return "false" as const;
    if (activeTab === "read") return "true" as const;
    return undefined;
  }, [activeTab]);

  const refresh = async () => {
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
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      setToken(localStorage.getItem("taurineToken") || "");
    }
  }, []);

  useEffect(() => {
    if (open) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, activeTab, token]);

  const openNotification = async (n: NetworkNotification) => {
    try {
      if (!n.read) await markNotificationRead(token, n.id);
    } catch (_) {
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

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-5 h-5 px-1 rounded-full bg-primary text-primary-foreground text-[10px] leading-5 text-center">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-96 p-0">
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between pr-12">
            <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabKey)}>
              <TabsList>
                <TabsTrigger value="unread">Unread</TabsTrigger>
                <TabsTrigger value="read">Read</TabsTrigger>
                <TabsTrigger value="all">All</TabsTrigger>
              </TabsList>
            </Tabs>
            <Button className="mr-2" variant="ghost" size="icon" aria-label="Refresh" onClick={refresh} disabled={loading}>
              <RefreshCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <ScrollArea className="h-[calc(100%-112px)]">
          <div className="divide-y">
            {(data?.results || []).map((n) => (
              <Card key={n.id} className="rounded-none shadow-none border-0">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 cursor-pointer" onClick={() => openNotification(n)}>
                      <p className="font-medium">
                        {n.type}
                        {!n.read && <span className="ml-2 inline-block h-2 w-2 rounded-full bg-primary align-middle" />}
                      </p>
                      <p className="text-sm text-muted-foreground">{n.description}</p>
                    </div>
                    {!n.read && (
                      <Button size="sm" onClick={() => onMarkRead(n)}>Mark as read</Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
            {!loading && data && data.count === 0 && (
              <div className="p-4 text-sm text-muted-foreground">No notifications.</div>
            )}
            {loading && (
              <div className="p-4 text-sm text-muted-foreground">Loading...</div>
            )}
          </div>
        </ScrollArea>
        <div className="px-4 py-2 border-t flex items-center justify-between text-xs text-muted-foreground">
          <div>
            View all in <button className="underline" onClick={() => { setOpen(false); router.push("/network-notifications"); }}>Network Notifications</button>
          </div>
          <Button variant="secondary" size="sm" onClick={onMarkAllRead}>Mark all as read</Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}


