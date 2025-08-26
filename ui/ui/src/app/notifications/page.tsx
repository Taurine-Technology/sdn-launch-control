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

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getTelegramNotifications } from "@/lib/telegramNotifications";
import { getUserData } from "@/lib/user";

import TelegramNotificationSetupDialog from "@/components/notifications/TelegramNotificationSetupDialog";
import TelegramNotificationList from "@/components/notifications/TelegramNotificationList";
import type { TelegramNotification, UserData } from "@/lib/types";
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
import { PlusIcon } from "lucide-react";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";

export default function NotificationsPage() {
  const { getT } = useLanguage();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState<UserData | null>(null);
  const [notifications, setNotifications] = useState<TelegramNotification[]>(
    []
  );
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  const fetchUserData = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      const data = await getUserData(token);
      setUserData(data);
    } catch (error) {
      console.error("Error fetching user data", error);
    }
  };

  const fetchNotifications = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    setNotificationsLoading(true);
    try {
      const data = await getTelegramNotifications(token);
      setNotifications(data);
    } catch (error) {
      console.error("Error fetching notifications", error);
    } finally {
      setNotificationsLoading(false);
    }
  };

  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([fetchUserData(), fetchNotifications()]);
      setLoading(false);
    };

    initializeData();
  }, []);

  const handleNotificationAdded = () => {
    fetchNotifications();
  };

  const handleOpenDialog = () => {
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const handleNotificationSuccess = () => {
    toast.success(getT("page.NotificationsPage.notification_created_success"));
    fetchNotifications();
  };

  const navigate = (path: string) => {
    router.push(path);
  };

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
                      {getT("navigation.settings", "Settings")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/notifications">
                      {getT("navigation.notifications", "Notifications")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="@container/main w-full max-w-7.5xl flex flex-col gap-6 px-4 lg:px-8 py-8 mx-auto">
            <div className="w-full flex flex-row items-end justify-between mb-6">
              <h1 className="text-2xl font-bold text-muted-foreground">
                {getT("page.NotificationsPage.title", "Telegram Notifications")}
              </h1>
              {!loading && userData?.profile.telegram_linked && (
                <div className="flex flex-col items-end gap-2">
                  <Button
                    className="mt-1 bg-taurine-dark-purple hover:bg-taurine-dark-purple/80"
                    onClick={handleOpenDialog}
                  >
                    <PlusIcon className="w-4 h-4" />
                    {getT("common.add", "Add")}{" "}
                    {getT("navigation.notifications", "Notifications")}
                  </Button>
                </div>
              )}
            </div>
            {loading && (
              <div className="w-full flex flex-col gap-4">
                <Skeleton className="h-25 w-full bg-muted-foreground/30" />
                <Skeleton className="h-25 w-full bg-muted-foreground/30" />
              </div>
            )}
            <div className="w-full flex flex-col gap-4">
              {userData?.profile.telegram_linked ? (
                <TelegramNotificationList
                  notifications={notifications}
                  loading={notificationsLoading}
                  onNotificationUpdate={handleNotificationAdded}
                />
              ) : (
                <Card className="w-full max-w-md mx-auto">
                  <CardContent className="p-6 text-center space-y-4">
                    <p className="text-muted-foreground">
                      {getT(
                        "page.NotificationsPage.link_telegram_message",
                        "Please link your Telegram account to receive notifications"
                      )}
                    </p>
                    <Button
                      onClick={() => navigate("/account")}
                      className="w-full"
                    >
                      {getT(
                        "page.NotificationsPage.link_telegram_button",
                        "Link Telegram Account"
                      )}
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
      <TelegramNotificationSetupDialog
        isOpen={dialogOpen}
        onClose={handleCloseDialog}
        onSuccess={handleNotificationSuccess}
      />
    </ProtectedRoute>
  );
}
