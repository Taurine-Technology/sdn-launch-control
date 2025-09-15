/*
 * File: networkNotifications.ts
 */
"use client";

import { createAxiosInstanceWithToken } from "./axiosInstance";
import type {
  NetworkNotification,
  PaginatedResponse,
} from "./types";

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


