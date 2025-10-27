/*
 * File: networkNotifications.ts
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
import type { NetworkNotification, PaginatedResponse } from "./types";

export interface NetworkNotificationsQuery {
  page?: number;
  page_size?: number;
  read?: "true" | "false"; // optional filter
}

export const listNetworkNotifications = async (
  token: string,
  params: NetworkNotificationsQuery = {}
): Promise<PaginatedResponse<NetworkNotification>> => {
  const axios = createAxiosInstanceWithToken(token);
  const query: string[] = [];
  if (params.page) query.push(`page=${params.page}`);
  if (params.page_size) query.push(`page_size=${params.page_size}`);
  if (params.read) query.push(`read=${params.read}`);
  const q = query.length ? `?${query.join("&")}` : "";
  const { data } = await axios.get(`/network-notifications/${q}`);
  // Normalize: backend may return a plain array or a paginated object
  if (Array.isArray(data)) {
    return {
      count: data.length,
      next: null,
      previous: null,
      results: data as NetworkNotification[],
    };
  }
  return data as PaginatedResponse<NetworkNotification>;
};

export const getNetworkNotification = async (
  token: string,
  id: number
): Promise<{ notification: NetworkNotification }> => {
  const axios = createAxiosInstanceWithToken(token);
  const { data } = await axios.get(`/network-notifications/${id}/`);
  // Backend returns the notification fields directly or wrapped
  if (data && typeof data === "object" && "id" in data) {
    return { notification: data as NetworkNotification };
  }
  return data as { notification: NetworkNotification };
};

export const markNotificationRead = async (
  token: string,
  id: number
): Promise<void> => {
  const axios = createAxiosInstanceWithToken(token);
  await axios.patch(`/network-notifications/${id}/`, { read: true });
};

export const markAllNotificationsRead = async (
  token: string
): Promise<void> => {
  const axios = createAxiosInstanceWithToken(token);
  await axios.post(`/network-notifications/read/all/`);
};
