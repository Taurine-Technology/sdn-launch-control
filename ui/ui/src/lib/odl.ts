/*
 * File: odl.ts
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
  OdlController,
  OdlNode,
  OdlMeter,
  OdlControllerApiResponse,
  OdlNodeApiResponse,
  OdlMeterApiResponse,
  CreateOdlMeterRequest,
  UpdateOdlMeterRequest,
  CreateOdlMeterResponse,
  UpdateOdlMeterResponse,
  NetworkDeviceSearchResponse,
} from "./types";

/**
 * Fetches OpenDaylight controllers from the backend.
 */
export const fetchOdlControllers = async (
  token: string
): Promise<OdlController[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  try {
    const response = await axiosInstance.get<OdlControllerApiResponse>(
      "/controllers/odl/"
    );
    // console.info("[ UTILS ] Fetched ODL Controllers:", response.data);
    return (response.data.results || response.data || []) as OdlController[];
  } catch (error) {
    console.error("Error fetching ODL controllers:", error);
    throw error;
  }
};

/**
 * Fetches the nodes (switches/bridges with ODL node IDs) managed by a specific ODL controller.
 * @param token - The authentication token.
 * @param controllerDbId - The database primary key of the general.models.Controller.
 */
export const fetchOdlControllerNodes = async (
  token: string,
  controllerDbId: number | string
): Promise<OdlNode[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  try {
    const response = await axiosInstance.get<OdlNodeApiResponse>(
      `/odl/controllers/${controllerDbId}/nodes/`
    );
    // console.info(
    //   `Fetched nodes for ODL Controller DB ID ${controllerDbId}:`,
    //   response.data
    // );
    return (response.data.results || response.data || []) as OdlNode[];
  } catch (error) {
    console.error(
      `Error fetching nodes for ODL Controller DB ID ${controllerDbId}:`,
      error
    );
    throw error;
  }
};

/**
 * Creates a new ODL meter.
 */
export const odlCreateMeter = async (
  token: string,
  payload: CreateOdlMeterRequest
): Promise<CreateOdlMeterResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post<CreateOdlMeterResponse>(
    "/odl/create-meter/",
    payload
  );
  console.log("[ ODL METER ] ODL Create Meter Response:", data);
  return data;
};

/**
 * Updates an existing ODL meter.
 */
export const odlUpdateMeter = async (
  token: string,
  meterDbId: number,
  payload: UpdateOdlMeterRequest
): Promise<UpdateOdlMeterResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.put<UpdateOdlMeterResponse>(
    `/odl/meters/${meterDbId}/`,
    payload
  );
  console.log("[ ODL METER ] ODL Update Meter Response:", data);
  return data;
};

/**
 * Deletes an ODL meter.
 */
export const odlDeleteMeter = async (
  token: string,
  meterDbId: number
): Promise<void> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.delete(`/odl/meters/${meterDbId}/`);
  console.log("[ ODL METER ] ODL Delete Meter Response:", data);
  return data;
};

/**
 * Fetches ODL meters for a specific switch.
 */
export const fetchOdlMetersForSwitch = async (
  token: string,
  controllerIp: string,
  switchNodeId: string,
  modelName?: string,
  includeLegacy?: boolean
): Promise<OdlMeter[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const params: Record<string, string> = {
    controller_ip: controllerIp,
    switch_node_id: switchNodeId,
  };

  if (modelName) {
    params.model_name = modelName;
  }
  if (includeLegacy) {
    params.include_legacy = "true";
  }

  const { data } = await axiosInstance.get<OdlMeterApiResponse>(
    "/odl/meters/",
    { params }
  );
  // console.log(
  //   `Fetched ODL Meters for ${switchNodeId} on ${controllerIp}:`,
  //   data
  // );
  return (data.results || data || []) as OdlMeter[];
};

/**
 * Searches for network devices.
 */
export const searchNetworkDevices = async (
  token: string,
  searchTerm: string,
  pageSize: number = 20
): Promise<NetworkDeviceSearchResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const params = [
    `search=${encodeURIComponent(searchTerm.trim())}`,
    `page_size=${pageSize}`,
  ];
  const query = `?${params.join("&")}`;
  const { data } = await axiosInstance.get<NetworkDeviceSearchResponse>(
    `/network-devices/${query}`
  );
  return data;
};
