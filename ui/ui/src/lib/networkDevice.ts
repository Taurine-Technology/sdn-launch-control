/*
 * File: networkDevice.ts
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

import { createAxiosInstanceWithToken } from "./axiosInstance";
import {
  NetworkDeviceApiResponse,
  NetworkDeviceDetailResponse,
  CreateNetworkDeviceRequest,
  UpdateNetworkDeviceRequest,
  NetworkDeviceQueryParams,
} from "./types";

/**
 * Fetches network devices with optional pagination, filtering, and search.
 */
export const fetchNetworkDevices = async (
  token: string,
  params?: NetworkDeviceQueryParams
): Promise<NetworkDeviceApiResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  // Build query parameters
  const queryParams = new URLSearchParams();
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        queryParams.append(key, String(value));
      }
    });
  }

  const queryString = queryParams.toString();
  const url = queryString
    ? `/network-devices/?${queryString}`
    : "/network-devices/";

  const { data } = await axiosInstance.get<NetworkDeviceApiResponse>(url);
  console.log("[ NETWORK DEVICES ] Fetched network devices:", data);
  return data;
};

/**
 * Creates a new network device.
 */
export const createNetworkDevice = async (
  token: string,
  payload: CreateNetworkDeviceRequest
): Promise<NetworkDeviceDetailResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post<NetworkDeviceDetailResponse>(
    "/network-devices/",
    payload
  );
  console.log("[ NETWORK DEVICES ] Created network device:", data);
  return data;
};

/**
 * Updates an existing network device (PATCH).
 */
export const updateNetworkDevice = async (
  token: string,
  id: number | string,
  payload: UpdateNetworkDeviceRequest
): Promise<NetworkDeviceDetailResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.patch<NetworkDeviceDetailResponse>(
    `/network-devices/${id}/`,
    payload
  );
  console.log(`[ NETWORK DEVICES ] Updated network device ${id}:`, data);
  return data;
};

/**
 * Deletes a network device.
 */
export const deleteNetworkDevice = async (
  token: string,
  id: number | string
): Promise<void> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  await axiosInstance.delete(`/network-devices/${id}/`);
  console.log(`[ NETWORK DEVICES ] Deleted network device ${id}`);
};

/**
 * Fetches a single network device by ID.
 */
export const fetchNetworkDevice = async (
  token: string,
  id: number | string
): Promise<NetworkDeviceDetailResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get<NetworkDeviceDetailResponse>(
    `/network-devices/${id}/`
  );
  console.log(`[ NETWORK DEVICES ] Fetched network device ${id}:`, data);
  return data;
};

/**
 * Searches for network devices by name, MAC address, or IP address.
 */
export const searchNetworkDevices = async (
  token: string,
  searchTerm: string,
  pageSize: number = 25
): Promise<NetworkDeviceApiResponse> => {
  return fetchNetworkDevices(token, {
    search: searchTerm,
    page_size: pageSize,
  });
};

/**
 * Fetches network devices with specific filters.
 */
export const fetchNetworkDevicesWithFilters = async (
  token: string,
  filters: Partial<NetworkDeviceQueryParams>
): Promise<NetworkDeviceApiResponse> => {
  return fetchNetworkDevices(token, filters);
};
