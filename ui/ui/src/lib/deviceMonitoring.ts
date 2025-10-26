/*
 * File: deviceMonitoring.ts
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

import { createAxiosInstanceWithToken } from "./axiosInstance";

// Types for device monitoring
export interface DevicePingStats {
  id: number;
  device: number;
  is_alive: boolean;
  successful_pings: number;
  timestamp: string;
}

export interface DeviceUptimeData {
  bucket: string;
  uptime_percentage: number;
  total_pings: number;
}

export interface DeviceAggregationData {
  device_id: number;
  uptime_percentage: number;
  total_pings: number;
  device_name?: string;
  is_monitored?: boolean;
  ip_address?: string;
  mac_address?: string;
}

export interface DeviceUptimeStatus {
  device_id: number;
  device_name: string;
  uptime_percentage: number;
  total_pings: number;
  is_monitored: boolean;
}

export interface ToggleMonitoringRequest {
  device_id: number;
  is_ping_target: boolean;
}

export interface IngestUptimeDataRequest {
  device_id: number;
  is_alive: boolean;
  successful_pings: number;
  timestamp?: string;
}

/**
 * Toggle device monitoring (enable/disable ping monitoring)
 */
export const toggleDeviceMonitoring = async (
  token: string,
  payload: ToggleMonitoringRequest
): Promise<{ success: boolean; message: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post(
    "/toggle-monitoring/",
    payload
  );
  console.log("[DEVICE MONITORING] Toggle monitoring:", data);
  return data;
};

/**
 * Get current uptime status for all monitored devices
 */
export const fetchDeviceUptimeStatus = async (
  token: string,
  period: string = "24 hours"
): Promise<DeviceUptimeStatus[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/uptime-status/?period=${encodeURIComponent(period)}`
  );
  console.log("[DEVICE MONITORING] Uptime status:", data);
  return data;
};

/**
 * Get time-series uptime data for a specific device
 */
export const fetchDeviceUptimeTimeseries = async (
  token: string,
  deviceId: number,
  period: string = "24 hours"
): Promise<DeviceUptimeData[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/uptime-line/?device_id=${deviceId}&period=${encodeURIComponent(period)}`
  );
  console.log("[DEVICE MONITORING] Uptime timeseries:", data);
  return data;
};

/**
 * Get aggregated uptime data for all devices
 */
export const fetchDeviceUptimeAggregates = async (
  token: string,
  period: string = "24 hours",
  minPings: number = 1
): Promise<DeviceAggregationData[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/uptime-aggregates/?period=${encodeURIComponent(period)}&min_pings=${minPings}`
  );
  console.log("[DEVICE MONITORING] Uptime aggregates:", data);
  return data;
};

/**
 * Get ping aggregates for all devices
 */
export const fetchPingAggregates = async (
  token: string,
  aggregation: string = "15m",
  timeRange: string = "24 hours"
): Promise<DeviceAggregationData[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/device-monitoring/ping-aggregates/?aggregation=${aggregation}&time_range=${encodeURIComponent(timeRange)}`
  );
  console.log("[DEVICE MONITORING] Ping aggregates:", data);
  return data;
};

/**
 * Get uptime line chart data
 */
export const fetchDeviceUptimeLineData = async (
  token: string,
  deviceId: number,
  timeRange: string = "24 hours"
): Promise<DeviceUptimeData[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/device-monitoring/uptime-line/?device_id=${deviceId}&time_range=${encodeURIComponent(timeRange)}`
  );
  console.log("[DEVICE MONITORING] Uptime line data:", data);
  return data;
};

/**
 * Ingest uptime data (for testing or external data sources)
 */
export const ingestUptimeData = async (
  token: string,
  payload: IngestUptimeDataRequest[]
): Promise<{ success: boolean; message: string; created_count: number }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post(
    "/ingest-uptime-data/",
    { data: payload }
  );
  console.log("[DEVICE MONITORING] Ingested uptime data:", data);
  return data;
};

/**
 * Get monitored devices (devices with is_ping_target=true)
 */
export const fetchMonitoredDevices = async (
  token: string
): Promise<DeviceUptimeStatus[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/network-devices/monitored/");
  console.log("[DEVICE MONITORING] Monitored devices:", data);
  return data;
};

/**
 * Update device name by IP or MAC address
 */
export const updateDeviceName = async (
  token: string,
  ipAddress: string | undefined,
  macAddress: string | undefined,
  newName: string
): Promise<{ message: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  
  const payload: { name: string; mac_address?: string; ip_address?: string } = { name: newName };
  if (macAddress) {
    payload.mac_address = macAddress;
  } else if (ipAddress) {
    payload.ip_address = ipAddress;
  } else {
    throw new Error("Either IP address or MAC address must be provided");
  }
  
  const { data } = await axiosInstance.put("/update-device/", payload);
  console.log("[DEVICE MONITORING] Updated device name:", data);
  return data;
};

/**
 * Delete device by IP or MAC address
 */
export const deleteDevice = async (
  token: string,
  ipAddress: string | undefined,
  macAddress: string | undefined
): Promise<{ message: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  
  const payload: { mac_address?: string; ip_address?: string } = {};
  if (macAddress) {
    payload.mac_address = macAddress;
  } else if (ipAddress) {
    payload.ip_address = ipAddress;
  } else {
    throw new Error("Either IP address or MAC address must be provided");
  }
  
  const { data } = await axiosInstance.delete("/delete-device/", { data: payload });
  console.log("[DEVICE MONITORING] Deleted device:", data);
  return data;
};