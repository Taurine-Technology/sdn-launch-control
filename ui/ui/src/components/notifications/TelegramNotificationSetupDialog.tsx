/*
 * File: TelegramNotificationSetupDialog.tsx
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { createTelegramNotification } from "@/lib/telegramNotifications";
import { useLanguage } from "@/context/languageContext";

import type {
  CreateTelegramNotificationRequest,
  NotificationType,
} from "@/lib/types";

interface TelegramNotificationSetupDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const TelegramNotificationSetupDialog: React.FC<
  TelegramNotificationSetupDialogProps
> = ({ isOpen, onClose, onSuccess }) => {
  const { getT } = useLanguage();
  const [isCreating, setIsCreating] = useState(false);

  const [newNotification, setNewNotification] =
    useState<CreateTelegramNotificationRequest>({
      type: "Network Summary",
      frequency: 60,
      top_users_count: 5,
      top_apps_count: 5,
      data_limit_mb: 100,
    });

  const handleChange = (
    field: keyof CreateTelegramNotificationRequest,
    value: string | number
  ) => {
    setNewNotification((prev) => ({ ...prev, [field]: value }));
  };

  const handleCreate = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    setIsCreating(true);

    try {
      await createTelegramNotification(token, newNotification);
      onSuccess();
      onClose();

      // Reset form
      setNewNotification({
        type: "Network Summary",
        frequency: 60,
        top_users_count: 5,
        top_apps_count: 5,
        data_limit_mb: 100,
      });
    } catch (error) {
      console.error("Error creating notification:", error);
      toast.error(
        getT(
          "components.notifications.telegram_notification_setup.error_creating"
        )
      );
    } finally {
      setIsCreating(false);
    }
  };

  const frequencyOptions = [
    {
      value: 1,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_minute"
      ),
    },
    {
      value: 10,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_10_minutes"
      ),
    },
    {
      value: 60,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_hour"
      ),
    },
    {
      value: 360,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_6_hours"
      ),
    },
    {
      value: 720,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_12_hours"
      ),
    },
    {
      value: 1440,
      label: getT(
        "components.notifications.telegram_notification_setup.frequency.every_24_hours"
      ),
    },
  ];

  const typeOptions = [
    {
      value: "Network Summary",
      label: getT(
        "components.notifications.telegram_notification_setup.type.network_summary"
      ),
    },
    {
      value: "Data Usage Alert",
      label: getT(
        "components.notifications.telegram_notification_setup.type.data_usage_alert"
      ),
    },
    {
      value: "Application Usage Alert",
      label: getT(
        "components.notifications.telegram_notification_setup.type.application_usage_alert"
      ),
    },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {getT("components.notifications.telegram_notification_setup.title")}
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="type">
              {getT(
                "components.notifications.telegram_notification_setup.notification_type"
              )}
            </Label>
            <Select
              value={newNotification.type}
              onValueChange={(value) =>
                handleChange("type", value as NotificationType)
              }
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={getT(
                    "components.notifications.telegram_notification_setup.select_notification_type"
                  )}
                />
              </SelectTrigger>
              <SelectContent>
                {typeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="frequency">
              {getT(
                "components.notifications.telegram_notification_setup.notification_frequency"
              )}
            </Label>
            <Select
              value={newNotification.frequency.toString()}
              onValueChange={(value) =>
                handleChange("frequency", parseInt(value))
              }
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={getT(
                    "components.notifications.telegram_notification_setup.select_frequency"
                  )}
                />
              </SelectTrigger>
              <SelectContent>
                {frequencyOptions.map((option) => (
                  <SelectItem
                    key={option.value}
                    value={option.value.toString()}
                  >
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {newNotification.type === "Network Summary" ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="top_users_count">
                  {getT(
                    "components.notifications.telegram_notification_setup.top_users_count"
                  )}
                </Label>
                <Input
                  id="top_users_count"
                  type="number"
                  value={newNotification.top_users_count}
                  onChange={(e) =>
                    handleChange("top_users_count", parseInt(e.target.value))
                  }
                  min="1"
                  max="20"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="top_apps_count">
                  {getT(
                    "components.notifications.telegram_notification_setup.top_apps_count"
                  )}
                </Label>
                <Input
                  id="top_apps_count"
                  type="number"
                  value={newNotification.top_apps_count}
                  onChange={(e) =>
                    handleChange("top_apps_count", parseInt(e.target.value))
                  }
                  min="1"
                  max="20"
                />
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="data_limit_mb">
                {getT(
                  "components.notifications.telegram_notification_setup.data_limit_mb"
                )}
              </Label>
              <Input
                id="data_limit_mb"
                type="number"
                value={newNotification.data_limit_mb}
                onChange={(e) =>
                  handleChange("data_limit_mb", parseInt(e.target.value))
                }
                min="1"
              />
            </div>
          )}

          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose} disabled={isCreating}>
              {getT(
                "components.notifications.telegram_notification_setup.cancel"
              )}
            </Button>
            <Button onClick={handleCreate} disabled={isCreating}>
              {isCreating
                ? getT(
                    "components.notifications.telegram_notification_setup.creating"
                  )
                : getT(
                    "components.notifications.telegram_notification_setup.create_notification"
                  )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TelegramNotificationSetupDialog;
