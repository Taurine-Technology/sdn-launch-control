/*
 * File: telegramNotifications.ts
 * Copyright (C) 2025 Taurine Technology
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Taurine Technology exclusive rights to
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

import { createAxiosInstanceWithToken } from "./axiosInstance";
import type {
  TelegramNotification,
  CreateTelegramNotificationRequest,
  UpdateTelegramNotificationRequest,
  NotificationType,
} from "./types";

export const getTelegramNotifications = async (
  token: string
): Promise<TelegramNotification[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const [summaryData, dataUsageData, appUsageData] = await Promise.all([
    axiosInstance.get("/network-summary/"),
    axiosInstance.get("/data-usage-alerts/"),
    axiosInstance.get("/app-usage-alerts/"),
  ]);

  return [
    ...summaryData.data.map((item: TelegramNotification) => ({
      ...item,
      type: "Network Summary" as NotificationType,
    })),
    ...dataUsageData.data.map((item: TelegramNotification) => ({
      ...item,
      type: "Data Usage Alert" as NotificationType,
    })),
    ...appUsageData.data.map((item: TelegramNotification) => ({
      ...item,
      type: "Application Usage Alert" as NotificationType,
    })),
  ];
};

export const createTelegramNotification = async (
  token: string,
  payload: CreateTelegramNotificationRequest
): Promise<TelegramNotification> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const endpoint =
    payload.type === "Network Summary"
      ? "/network-summary/"
      : payload.type === "Data Usage Alert"
      ? "/data-usage-alerts/"
      : "/app-usage-alerts/";

  const { data } = await axiosInstance.post(endpoint, payload);
  return data;
};

export const updateTelegramNotification = async (
  token: string,
  id: number,
  payload: UpdateTelegramNotificationRequest
): Promise<TelegramNotification> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const endpoint =
    payload.type === "Network Summary"
      ? `/network-summary/${id}/`
      : payload.type === "Data Usage Alert"
      ? `/data-usage-alerts/${id}/`
      : `/app-usage-alerts/${id}/`;

  const { data } = await axiosInstance.put(endpoint, payload);
  return data;
};

export const deleteTelegramNotification = async (
  token: string,
  id: number,
  type: NotificationType
): Promise<void> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const endpoint =
    type === "Network Summary"
      ? `/network-summary/${id}/`
      : type === "Data Usage Alert"
      ? `/data-usage-alerts/${id}/`
      : `/app-usage-alerts/${id}/`;

  await axiosInstance.delete(endpoint);
};
