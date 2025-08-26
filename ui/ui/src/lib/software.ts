import { createAxiosInstanceWithToken } from "./axiosInstance";
import {
  InstallControllerRequest,
  InstallControllerResponse,
  InstallPluginOnLCRequest,
  InstallPluginOnLCResponse,
  InstallSnifferRequest,
  InstallSnifferResponse,
  SnifferInstallationConfig,
  UpdateSnifferConfigRequest,
  Plugin,
  PluginInstallation,
} from "./types";

export const installController = async (
  token: string,
  controller_type: string,
  payload: InstallControllerRequest
): Promise<InstallControllerResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const { data } = await axiosInstance.post(
    `/install-controller/${controller_type}/`,
    payload
  );
  return data;
};

// Plugins

export const fetchPlugins = async (token: string): Promise<Plugin[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/plugins/");

  return data;
};

export const fetchInstalledPlugins = async (
  token: string
): Promise<PluginInstallation[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/installations/");

  return data;
};

export const installPluginOnLC = async (
  token: string,
  payload: { plugin: number }
): Promise<InstallPluginOnLCResponse> => {
  // Install plugin on SDN Launch Control
  // payload: { "plugin": 1}
  const installPayload: InstallPluginOnLCRequest = {
    plugin_id: payload.plugin, // Assuming payload had { plugin: id }
    device_id: null, // Explicitly null for server install
  };
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.post("/installations/", installPayload);

  return data;
};

export const uninstallPluginOnLC = async (
  token: string,
  installationId: number
): Promise<boolean> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.delete(
    `/installations/${installationId}/`
  );

  return response.status === 204;
};

// --- Sniffer Specific Endpoints ---

// Installs the sniffer plugin (Calls the custom action in PluginViewSet)
// Payload remains the same as before
export const installSniffer = async (
  token: string,
  payload: InstallSnifferRequest
): Promise<InstallSnifferResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.post(
    `/plugins/install-sniffer/`,
    payload
  );
  // Response includes { status, message, config } on success
  return response.data;
};

// Fetches ONLY sniffer configurations (Calls the dedicated Sniffer Config ViewSet)
export const fetchSnifferConfigs = async (
  token: string
): Promise<SnifferInstallationConfig[]> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.get(`/sniffer-configs/`);
  // Returns array of SnifferInstallationConfig objects
  return response.data;
};

// Updates a specific sniffer configuration (Calls the dedicated Sniffer Config ViewSet)
// Note: The ID here is the installation ID (which is the PK for SnifferInstallationConfig)
export const updateSnifferConfig = async (
  token: string,
  installationId: number,
  payload: UpdateSnifferConfigRequest
): Promise<SnifferInstallationConfig> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.put(
    `/sniffer-configs/${installationId}/`, // Update endpoint for config
    payload
  );
  // Returns the updated SnifferInstallationConfig object
  return response.data;
};

// Deletes a specific sniffer configuration AND its parent installation
// (Calls the dedicated Sniffer Config ViewSet destroy method)
// Note: The ID here is the installation ID (which is the PK for SnifferInstallationConfig)
export const deleteSnifferInstallation = async (
  token: string,
  installationId: number
): Promise<boolean> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.delete(
    `/sniffer-configs/${installationId}/`
  );
  return response.status === 204;
};
