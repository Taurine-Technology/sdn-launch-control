/*
 * File: deviceMonitoring.ts
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
  DeviceUptimeStatus,
  DevicePingStats,
  DeviceUptimeData,
  DeviceAggregationData,
  ToggleMonitoringRequest,
  IngestUptimeDataRequest,
} from "./types";

// Functions for device monitoring

/**
 * Toggle device monitoring (enable/disable ping monitoring)
 */
export const toggleDeviceMonitoring = async (
  token: string,
  payload: ToggleMonitoringRequest
): Promise<{ success: boolean; message: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.patch(
    `/network-devices/${payload.device_id}/`,
    { is_ping_target: payload.is_ping_target }
  );
  // console.log("[DEVICE MONITORING] Toggle monitoring:", data);
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
    `/uptime/?period=${encodeURIComponent(period)}`
  );
  // console.log("[DEVICE MONITORING] Uptime status:", data);
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
    `/uptime/${deviceId}/timeseries/?period=${encodeURIComponent(period)}`
  );
  // console.log("[DEVICE MONITORING] Uptime timeseries:", data);
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
    `/uptime/?period=${encodeURIComponent(period)}&min_pings=${minPings}`
  );
  // console.log("[DEVICE MONITORING] Uptime aggregates:", data);
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
    `/uptime/aggregates/?aggregation=${aggregation}&time_range=${encodeURIComponent(
      timeRange
    )}`
  );
  // console.log("[DEVICE MONITORING] Ping aggregates:", data);
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
  // console.log("[DEVICE MONITORING] Monitored devices:", data);
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

  // Determine the identifier to use in the URL
  let identifier: string;
  if (macAddress) {
    identifier = macAddress;
  } else if (ipAddress) {
    identifier = ipAddress;
  } else {
    throw new Error("Either IP address or MAC address must be provided");
  }

  const { data } = await axiosInstance.patch(
    `/network-devices/${encodeURIComponent(identifier)}/`,
    {
      name: newName,
    }
  );
  // console.log("[DEVICE MONITORING] Updated device name:", data);
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

  // Determine the identifier to use in the URL
  let identifier: string;
  if (macAddress) {
    identifier = macAddress;
  } else if (ipAddress) {
    identifier = ipAddress;
  } else {
    throw new Error("Either IP address or MAC address must be provided");
  }

  const { data } = await axiosInstance.delete(
    `/network-devices/${encodeURIComponent(identifier)}/`
  );
  // console.log("[DEVICE MONITORING] Deleted device:", data);
  return data;
};

export const createNetworkDevice = async (
  token: string,
  deviceData: {
    name: string;
    device_type: string;
    operating_system: string;
    ip_address: string;
    mac_address?: string;
    is_ping_target: boolean;
  }
): Promise<{ success: boolean; message: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/network-devices/", deviceData);
  // console.log("[DEVICE MONITORING] Created device:", data);
  return data;
};
