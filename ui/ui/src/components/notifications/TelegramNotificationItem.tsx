/*
 * File: TelegramNotificationItem.tsx
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

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { deleteTelegramNotification } from "@/lib/telegramNotifications";
import { toast } from "sonner";
import type { TelegramNotification } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

interface TelegramNotificationItemProps {
  notification: TelegramNotification;
  onDelete: () => void;
}

const TelegramNotificationItem: React.FC<TelegramNotificationItemProps> = ({
  notification,
  onDelete,
}) => {
  const { getT } = useLanguage();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    setIsDeleting(true);
    try {
      await deleteTelegramNotification(
        token,
        notification.id,
        notification.type
      );
      toast.success(
        getT(
          "components.notifications.telegram_notification_item.delete_success"
        )
      );
      onDelete();
    } catch (error) {
      console.error("Error deleting notification:", error);
      toast.error(
        getT("components.notifications.telegram_notification_item.delete_error")
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const getFrequencyLabel = (frequency: number): string => {
    switch (frequency) {
      case 1:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_minute"
        );
      case 10:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_10_minutes"
        );
      case 60:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_hour"
        );
      case 360:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_6_hours"
        );
      case 720:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_12_hours"
        );
      case 1440:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_24_hours"
        );
      default:
        return getT(
          "components.notifications.telegram_notification_item.frequency_options.every_x_minutes",
          `Every ${frequency} minutes`
        );
    }
  };

  const getTypeColor = (type: string): string => {
    switch (type) {
      case "Network Summary":
        return "bg-blue-500";
      case "Data Usage Alert":
        return "bg-orange-500";
      case "Application Usage Alert":
        return "bg-purple-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <Card className="w-full mb-1">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge className={getTypeColor(notification.type)}>
              {notification.type}
            </Badge>
            <CardTitle className="text-md">
              {getFrequencyLabel(notification.frequency)}
            </CardTitle>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" size="sm" disabled={isDeleting}>
                {isDeleting
                  ? getT(
                      "components.notifications.telegram_notification_item.deleting"
                    )
                  : getT(
                      "components.notifications.telegram_notification_item.delete"
                    )}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>
                  {getT(
                    "components.notifications.telegram_notification_item.delete_notification"
                  )}
                </AlertDialogTitle>
                <AlertDialogDescription>
                  {getT(
                    "components.notifications.telegram_notification_item.delete_confirmation_message"
                  )}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>
                  {getT(
                    "components.notifications.telegram_notification_item.cancel"
                  )}
                </AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                >
                  {getT(
                    "components.notifications.telegram_notification_item.delete"
                  )}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {notification.type === "Network Summary" && (
            <>
              <div className="text-sm">
                <span className="text-muted-foreground">
                  {getT(
                    "components.notifications.telegram_notification_item.top_users_count"
                  )}
                  :{" "}
                </span>
                <span className="font-medium">
                  {notification.top_users_count}
                </span>
              </div>
              <div className="text-sm">
                <span className="text-muted-foreground">
                  {getT(
                    "components.notifications.telegram_notification_item.top_apps_count"
                  )}
                  :{" "}
                </span>
                <span className="font-medium">
                  {notification.top_apps_count}
                </span>
              </div>
            </>
          )}
          {(notification.type === "Data Usage Alert" ||
            notification.type === "Application Usage Alert") && (
            <div className="text-sm">
              <span className="text-muted-foreground">
                {getT(
                  "components.notifications.telegram_notification_item.data_limit"
                )}
                :{" "}
              </span>
              <span className="font-medium">
                {notification.data_limit_mb} MB
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TelegramNotificationItem;
