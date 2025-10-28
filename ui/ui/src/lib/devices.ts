/*
 * File: devices.ts
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
  NetworkDeviceDetails,
  Device,
  Controller,
  Bridge,
  BridgeApiResponse,
  DeleteDeviceRequest,
  DeleteDeviceResponse,
} from "./types";

export const fetchNetworkDevices = async (
  token: string
): Promise<{ results: NetworkDeviceDetails[] } | NetworkDeviceDetails[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const { data } = await axiosInstance.get("/network-devices/");

  return data;
};

export const fetchDevices = async (token: string): Promise<Device[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/devices/");
  console.log("[DEVICES.ts] fetchDevices", data);
  return data;
};
// this is the original function for devices
export const fetchNetworkDevice = async (
  token: string,
  id: string
): Promise<NetworkDeviceDetails> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  console.log("[DEVICES.ts] fetchNetworkDevice", id);
  const { data } = await axiosInstance.get(`/device-details/${id}/`);
  console.log("[DEVICES.ts] fetchNetworkDevice result", data);
  return data;
};

export const createNetworkDevice = async (
  token: string,
  payload: Partial<NetworkDeviceDetails>
): Promise<NetworkDeviceDetails> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/network-devices/", payload);
  return data;
};

export const updateNetworkDevice = async (
  token: string,
  id: string,
  payload: Partial<NetworkDeviceDetails>
): Promise<NetworkDeviceDetails> => {
  console.log("[DEVICES.ts] updateNetworkDevice", id, payload);
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.patch(
    `/network-devices/${id}/`,
    payload
  );
  console.log("[DEVICES.ts] updateNetworkDevice result", data);
  return data;
};

export const deleteNetworkDevice = async (
  token: string,
  id: string
): Promise<unknown> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.delete(`/network-devices/${id}/`);
  return data;
};

// Switches
export const fetchSwitches = async (
  token: string
): Promise<{ results: NetworkDeviceDetails[] } | NetworkDeviceDetails[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/switches/");
  // console.log("[DEVICES.ts] fetchSwitches", data);
  return data;
};

export const updateSwitch = async (
  token: string,
  id: string,
  deviceData: Partial<NetworkDeviceDetails>
): Promise<NetworkDeviceDetails> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.put(`/switches/${id}/`, deviceData);
  console.log("[DEVICES.ts] updateSwitch result", data);
  return data;
};

// OVS methods
export const installOvs = async (
  token: string,
  deviceData: Record<string, unknown>
): Promise<{ message: string; status: string }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/install-ovs/", deviceData);
  return data;
};

export const fetchBridges = async (
  token: string,
  id: string
): Promise<BridgeApiResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(`/switches/${id}/bridges/`);
  console.log("[DEVICES.ts] fetchBridges", data);
  return data;
};

export const fetchBridgesFromDevice = async (
  token: string,
  deviceIp: string
): Promise<Bridge[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(`/get-bridges/${deviceIp}/`);
  return data;
};

export const addBridge = async (
  token: string,
  bridgeData: Partial<Bridge>
): Promise<Bridge> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  console.log("[DEVICES.ts] addBridge", bridgeData);
  const { data } = await axiosInstance.post("/add-bridge/", bridgeData);
  console.log("[DEVICES.ts] addBridge result", data);
  return data;
};

export const updateBridge = async (
  token: string,
  bridgeData: Partial<Bridge>
): Promise<Bridge> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.put("/update-bridge/", bridgeData);
  return data;
};

export const deleteBridge = async (
  token: string,
  bridgeData: { name: string; lan_ip_address: string }
): Promise<unknown> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/delete-bridge/", bridgeData);
  return data;
};

// Controller methods

export const fetchControllers = async (
  token: string
): Promise<Controller[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/controllers/");
  return data;
};

export const fetchController = async (
  token: string,
  id: string
): Promise<Controller> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(`/controllers/${id}/`);
  // console.log(data);
  return data;
};

export const updateController = async (
  token: string,
  id: string,
  updatedController: Partial<Controller>
): Promise<Controller> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.put(
    `/controllers/${id}/`,
    updatedController
  );
  return data;
};

export const deleteController = async (
  token: string,
  payload: DeleteDeviceRequest
): Promise<DeleteDeviceResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.delete("/delete-device/", {
    data: payload,
  });
  console.log("[DEVICES.ts] deleteController result", response);

  // Django returns 204 No Content on successful deletion
  if (response.status === 204) {
    return {
      status: "success",
      message: "Controller deleted successfully",
    };
  }

  // If there's a response body, return it
  return (
    response.data || {
      status: "error",
      message: "Unknown error occurred",
    }
  );
};

export const forceDeleteController = async (
  token: string,
  payload: { name: string; lan_ip_address: string }
): Promise<unknown> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.delete("/force-delete-device/", {
    data: payload,
  });
  // console.log(data);
  return data;
};

// Port methods
export const fetchUnassignedPorts = async (
  token: string,
  deviceIp: string
): Promise<{ status: string; interfaces?: string[] }> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get(
    `/unassigned-device-ports/${deviceIp}/`
  );
  return data;
};

// QoS methods
export const installQosMonitoring = async (
  token: string,
  payload: Record<string, unknown>
): Promise<unknown> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post(
    "/install-ovs-qos-monitor/",
    payload
  );
  return data;
};

// Switch deletion methods
export const deleteSwitch = async (
  token: string,
  payload: { lan_ip_address: string }
): Promise<DeleteDeviceResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.delete("/delete-device/", {
    data: payload,
  });
  console.log("[DEVICES.ts] deleteSwitch result", response);

  // Django returns 204 No Content on successful deletion
  if (response.status === 204) {
    return {
      status: "success",
      message: "Switch deleted successfully",
    };
  }

  // If there's a response body, return it
  return (
    response.data || {
      status: "error",
      message: "Unknown error occurred",
    }
  );
};

export const forceDeleteSwitch = async (
  token: string,
  payload: { lan_ip_address: string }
): Promise<DeleteDeviceResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.delete("/force-delete-device/", {
    data: payload,
  });
  console.log("[DEVICES.ts] forceDeleteSwitch result", response);

  // Django returns 204 No Content on successful deletion
  if (response.status === 204) {
    return {
      status: "success",
      message: "Switch force deleted successfully",
    };
  }

  // If there's a response body, return it
  return (
    response.data || {
      status: "error",
      message: "Unknown error occurred",
    }
  );
};
