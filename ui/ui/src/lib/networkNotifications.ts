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
  return data as PaginatedResponse<NetworkNotification>;
};

export const getNetworkNotification = async (
  token: string,
  id: number
): Promise<{ notification: NetworkNotification }> => {
  const axios = createAxiosInstanceWithToken(token);
  const { data } = await axios.get(`/network-notifications/${id}/`);
  return data as { notification: NetworkNotification };
};

export const markNotificationRead = async (
  token: string,
  id: number
): Promise<void> => {
  const axios = createAxiosInstanceWithToken(token);
  await axios.get(`/network-notifications/read/${id}/`);
};

export const markAllNotificationsRead = async (
  token: string
): Promise<void> => {
  const axios = createAxiosInstanceWithToken(token);
  await axios.get(`/network-notifications/read/all/`);
};


