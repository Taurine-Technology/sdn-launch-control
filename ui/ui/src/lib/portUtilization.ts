/*
 * File: portUtilization.ts
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

import { createAxiosInstanceWithToken } from "./axiosInstance";
import {
  AllDevicesPortStatsResponse,
  AggregatePortStatsResponse,
} from "./types";

/**
 * Fetches port utilization statistics for all devices
 * @param token - Authentication token
 * @param hours - Optional number of hours to fetch (defaults to 24 on backend)
 * @returns All devices with their port statistics
 */
export const fetchAllDevicesPortStats = async (
  token: string,
  hours?: number
): Promise<AllDevicesPortStatsResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const params = new URLSearchParams();
  if (hours !== undefined) {
    params.append("hours", hours.toString());
  }

  const url = params.toString()
    ? `/port-utilization-stats/all-devices/?${params.toString()}`
    : "/port-utilization-stats/all-devices/";

  const { data } = await axiosInstance.get<AllDevicesPortStatsResponse>(url);
  console.log("[portUtilization] All devices port stats:", data);
  return data;
};

/**
 * Fetches time-series port utilization statistics using the aggregate endpoint
 * @param token - Authentication token
 * @param ipAddress - Device IP address (optional - omit for all devices)
 * @param hours - Number of hours to fetch
 * @param interval - Time bucket interval (e.g., "10 seconds", "1 minute", "5 minutes")
 * @param signal - Optional AbortSignal for request cancellation
 * @returns Aggregated time series data
 */
export const fetchPortStatsAggregate = async (
  token: string,
  ipAddress: string | null,
  hours: number,
  interval: string,
  signal?: AbortSignal
): Promise<AggregatePortStatsResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const params = new URLSearchParams({
    hours: hours.toString(),
    interval: interval,
  });

  // Only add ip_address if provided (for single device queries)
  if (ipAddress) {
    params.append("ip_address", ipAddress);
  }

  const url = `/port-utilization-stats/aggregate/?${params.toString()}`;

  const { data } = await axiosInstance.get<AggregatePortStatsResponse>(url, {
    signal,
  });
  console.log(
    `[portUtilization] Aggregate stats${
      ipAddress ? ` for ${ipAddress}` : " for all devices"
    }:`,
    data
  );
  return data;
};
