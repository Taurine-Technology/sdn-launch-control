/*
 * File: deviceStats.ts
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
import { AggregateDeviceStatsResponse } from "./types";

/**
 * Fetches time-series device stats (CPU, memory, disk) using the aggregate endpoint
 * @param token - Authentication token
 * @param ipAddress - Device IP address (required)
 * @param hours - Number of hours to fetch
 * @param interval - Time bucket interval (e.g., "10 seconds", "1 minute", "5 minutes")
 * @param signal - Optional AbortSignal for request cancellation
 */
export const fetchDeviceStatsAggregate = async (
  token: string,
  ipAddress: string,
  hours: number,
  interval: string,
  signal?: AbortSignal
): Promise<AggregateDeviceStatsResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const params = new URLSearchParams({
    ip_address: ipAddress,
    hours: hours.toString(),
    interval,
  });

  const url = `/device-stats/aggregate/?${params.toString()}`;
  const { data } = await axiosInstance.get<AggregateDeviceStatsResponse>(url, {
    signal,
  });
  return data;
};
