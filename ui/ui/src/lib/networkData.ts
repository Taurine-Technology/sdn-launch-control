/*
 * File: networkData.ts
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
import {
  HistoricalClassificationData,
  AggregatedDataPerUserData,
  MacAddressClassificationData,
  UserFlowData,
  DataPerClassificationData,
} from "./types";

export const fetchHistoricalClassificationData = async (
  token: string,
  period: string
): Promise<HistoricalClassificationData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `network/aggregate-flows/?period=${encodeURIComponent(period)}`
  );
  console.log("[networkData] aggregated flow data: ", data);
  return data;
};

export const fetchAggregateFlowsByUser = async (
  token: string,
  period: string
): Promise<AggregatedDataPerUserData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `network/data-per-user/?period=${encodeURIComponent(period)}`
  );
  console.log("[networkData] aggregated flow data by user: ", data);
  return data;
};

export const fetchAggregateFlowsByMac = async (
  token: string,
  period: string,
  macAddress: string
): Promise<MacAddressClassificationData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `network/aggregate-flows-mac/?period=${encodeURIComponent(
      period
    )}&mac_address=${encodeURIComponent(macAddress)}`
  );
  console.log("[networkData] aggregated flow data by MAC: ", data);
  return data;
};

export const fetchUserFlowData = async (
  token: string,
  period: string
): Promise<UserFlowData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `network/user-flow-data/?period=${encodeURIComponent(period)}`
  );
  console.log("[networkData] user flow data:", data);
  return data;
};

export const fetchDataPerClassification = async (
  token: string,
  period: string
): Promise<DataPerClassificationData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `network/data-per-classification/?period=${encodeURIComponent(period)}`
  );
  console.log("[networkData] data per classification:", data);
  return data;
};
