/*
 * File: TelegramNotificationSetupComponent.tsx
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

import type {
  CreateTelegramNotificationRequest,
  NotificationType,
} from "@/lib/types";

interface TelegramNotificationSetupComponentProps {
  onNotificationAdded: () => void;
}

const TelegramNotificationSetupComponent: React.FC<
  TelegramNotificationSetupComponentProps
> = ({ onNotificationAdded }) => {
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
      toast.success("Notification created successfully!");
      onNotificationAdded();

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
      toast.error("Error creating notification");
    } finally {
      setIsCreating(false);
    }
  };

  const frequencyOptions = [
    { value: 1, label: "Every minute" },
    { value: 10, label: "Every 10 minutes" },
    { value: 60, label: "Every hour" },
    { value: 360, label: "Every 6 hours" },
    { value: 720, label: "Every 12 hours" },
    { value: 1440, label: "Every 24 hours" },
  ];

  const typeOptions = [
    { value: "Network Summary", label: "Network Summary" },
    { value: "Data Usage Alert", label: "Data Usage Alert" },
    { value: "Application Usage Alert", label: "Application Usage Alert" },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create New Notification</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="type">Notification Type</Label>
          <Select
            value={newNotification.type}
            onValueChange={(value) =>
              handleChange("type", value as NotificationType)
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select notification type" />
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
          <Label htmlFor="frequency">Notification Frequency</Label>
          <Select
            value={newNotification.frequency.toString()}
            onValueChange={(value) =>
              handleChange("frequency", parseInt(value))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select frequency" />
            </SelectTrigger>
            <SelectContent>
              {frequencyOptions.map((option) => (
                <SelectItem key={option.value} value={option.value.toString()}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {newNotification.type === "Network Summary" ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="top_users_count">Top Users Count</Label>
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
              <Label htmlFor="top_apps_count">Top Apps Count</Label>
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
            <Label htmlFor="data_limit_mb">Data Limit (MB)</Label>
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

        <Button onClick={handleCreate} disabled={isCreating} className="w-full">
          {isCreating ? "Creating..." : "Create Notification"}
        </Button>
      </CardContent>
    </Card>
  );
};

export default TelegramNotificationSetupComponent;
