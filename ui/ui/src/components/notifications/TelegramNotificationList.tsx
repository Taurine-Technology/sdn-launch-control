/*
 * File: TelegramNotificationList.tsx
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

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import TelegramNotificationItem from "./TelegramNotificationItem";
import type { TelegramNotification } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

interface TelegramNotificationListProps {
  notifications: TelegramNotification[];
  loading: boolean;
  onNotificationUpdate: () => void;
}

const TelegramNotificationList: React.FC<TelegramNotificationListProps> = ({
  notifications,
  loading,
  onNotificationUpdate,
}) => {
  const { getT } = useLanguage();
  if (loading) {
    return (
      <div className="w-full flex items-center justify-center flex-col gap-4">
        <div className="relative grid grid-cols-1 @xl/main:grid-cols-2 gap-4 w-full">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="h-[320px] w-full">
              <CardContent className="space-y-4 p-6">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full flex items-center justify-center flex-col gap-4">
      <div className="relative grid grid-cols-1 @xl/main:grid-cols-2 gap-4 w-full">
        {notifications.length > 0 ? (
          notifications.map((notification) => (
            <TelegramNotificationItem
              key={`${notification.type}_${notification.id}`}
              notification={notification}
              onDelete={onNotificationUpdate}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-8 text-muted-foreground">
            {getT(
              "components.notifications.telegram_notification_list.no_active_notifications"
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TelegramNotificationList;
