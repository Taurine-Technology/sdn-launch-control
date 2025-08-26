/*
 * File: types.ts
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
import { ReactNode } from "react";

export interface AuthContextType {
  isAuthenticated: boolean;
  authenticate: (token: string, username: string) => void;
  logout: (sessionExpiredFlag?: boolean) => void;
  loading: boolean;
  username?: string | null;
  token?: string | null;
}

export interface AuthProviderProps {
  children: ReactNode;
}

export interface LoginResponse {
  token: string;
  username: string;
}

// --- Network Diagram Types ---
export type NetworkNodeType =
  | "device"
  | "switch"
  | "controller"
  | "access_point"
  | "default";

export interface NetworkNode {
  id: string;
  type: NetworkNodeType;
  hostName?: string;
  bridgeName?: string;
  displayName?: string;
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
}

export interface NetworkLink {
  source: string;
  target: string;
}

export interface NetworkMapData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

// Device details for device info panel
export interface NetworkDeviceDetails {
  id: string;
  name: string;
  mac_address: string;
  ip_address?: string;
  lan_ip_address?: string;
  device_type?: string;
  operating_system?: string;
  verified?: boolean;
  number_of_ports?: number;
  [key: string]: unknown;
}

export interface InstallOvsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (payload: Record<string, unknown>) => Promise<void>;
  switches: NetworkDeviceDetails[];
  isLoading: boolean;
  response?: string;
  responseType?: "success" | "error";
}

// --- Django Model Types ---

// Device Types
export type DeviceType =
  | "switch"
  | "access_point"
  | "server"
  | "controller"
  | "vm";
export type OsType =
  | "ubuntu_20_server"
  | "ubuntu_22_server"
  | "unknown"
  | "other";

export interface Device {
  id: number;
  name: string;
  device_type: DeviceType;
  os_type: OsType;
  username?: string | null;
  password?: string | null;
  lan_ip_address: string;
  num_ports: number;
  ovs_enabled: boolean;
  ovs_version?: string | null;
  openflow_version?: string | null;
}

// Controller Types
export type ControllerType = "onos" | "odl" | "faucet" | "unknown" | "other";

export interface Controller {
  id: number;
  name: string;
  type: ControllerType;
  device: Device;
  port_num: number;
  lan_ip_address?: string | null;
}

// Port Types
export interface Port {
  id: number;
  name: string;
  ovs_port_number?: number | null;
  bridge?: number | null;
  device: number;
}

// Bridge Types
export interface Bridge {
  id: number;
  name: string;
  dpid: string;
  odl_node_id?: string | null;
  device: Device;
  ports: Port[];
  controller?: Controller | null;
  api_url?: string | null;
}

// Plugin Types
export interface Plugin {
  id: number;
  alias: string;
  name: string;
  version: string;
  short_description: string;
  long_description: string;
  author: string;
  installed: boolean;
  target_devices: Device[];
  requires_target_device: boolean;
}

// Classifier Types
export interface Classifier {
  id: number;
  name: string;
  number_of_bytes: number;
  number_of_packets: number;
  categories: string;
}

// API Response Types
export interface BridgeApiResponse {
  bridges: Bridge[];
  status?: string;
  message?: string;
}

export interface DeviceApiResponse {
  devices: Device[];
  status?: string;
  message?: string;
}

export interface ControllerApiResponse {
  controllers: Controller[];
  status?: string;
  message?: string;
}

export interface PluginApiResponse {
  plugins: Plugin[];
  status?: string;
  message?: string;
}

// Legacy types for backward compatibility
export interface BridgeData {
  status?: string;
  message?: string;
  bridges: Bridge[];
}

// Delete Device/Controller Types
export interface DeleteDeviceRequest {
  lan_ip_address: string;
}

export interface DeleteDeviceResponse {
  status: "success" | "error" | "failed";
  message?: string;
}

// --- Controller Installation Types ---

// Install Controller Request/Response Types
export interface InstallControllerRequest {
  name: string;
  lan_ip_address: string;
  username: string;
  password: string;
  os_type: string;
  device_type: string;
}

export interface InstallControllerResponse {
  status: "success" | "error";
  message: string;
}

// --- Plugin Installation Types ---

// Plugin Installation on Launch Control
export interface InstallPluginOnLCRequest {
  plugin_id: number;
  device_id: number | null; // null for server install
}

export interface InstallPluginOnLCResponse {
  id: number;
  plugin: number;
  device: number | null;
  installed_at: string;
  status: "installed" | "failed" | "pending";
}

// Sniffer Installation Types
export interface InstallSnifferRequest {
  lan_ip_address: string;
  api_base_url: string;
  monitor_interface: string;
  port_to_client: string;
  port_to_router: string;
  bridge_name: string;
}

export interface InstallSnifferResponse {
  status: "success" | "error";
  message: string;
  config?: SnifferInstallationConfig;
}

// Sniffer Configuration Types
export interface SnifferInstallationConfig {
  id: number;
  installation: number; // PluginInstallation ID
  api_base_url: string;
  monitor_interface: string;
  port_to_client: string;
  port_to_router: string;
  bridge_name: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateSnifferConfigRequest {
  api_base_url?: string;
  monitor_interface?: string;
  port_to_client?: string;
  port_to_router?: string;
  bridge_name?: string;
}

// Plugin Installation Record
export interface PluginInstallation {
  id: number;
  plugin: Plugin;
  device: Device | null; // null for server installations
  installed_at: string;
  status: "installed" | "failed" | "pending";
  sniffer_config?: SnifferInstallationConfig | null;
  plugin_name?: string;
}

// API Response Types for Plugins
export interface PluginInstallationApiResponse {
  installations: PluginInstallation[];
  status?: string;
  message?: string;
}

export interface SnifferConfigApiResponse {
  configs: SnifferInstallationConfig[];
  status?: string;
  message?: string;
}

// Generic API Response Type
export interface ApiResponse<T> {
  status: "success" | "error";
  message?: string;
  data?: T;
}

// Plugin Requirement Types (if needed)
export interface PluginRequirement {
  id: number;
  plugin: number;
  requirement_name: string;
  requirement_version: string;
  requirement_type: "python_package" | "system_package" | "other";
}

// Plugin Installation Status Types
export type PluginInstallationStatus =
  | "installed"
  | "failed"
  | "pending"
  | "uninstalling";

// Plugin Target Device Types
export type PluginTargetDevice = "switch" | "controller" | "server" | "all";

// Plugin Category Types
export type PluginCategory =
  | "monitoring"
  | "security"
  | "traffic_control"
  | "analysis"
  | "other";

// Extended Plugin interface with additional fields
export interface ExtendedPlugin extends Plugin {
  category?: PluginCategory;
  requirements?: PluginRequirement[];
  target_device_types?: PluginTargetDevice[];
  installation_count?: number;
  last_updated?: string;
  is_active?: boolean;
}

// --- ODL Meter Types ---
export interface OdlMeter {
  id: number;
  controller_device: Device;
  meter_id_on_odl: string;
  meter_type: string;
  rate: number;
  switch_node_id: string;
  odl_flags: string;
  network_device?: number | null;
  network_device_mac?: string | null;
  activation_period: "all_week" | "weekday" | "weekend";
  start_time?: string | null;
  end_time?: string | null;
  categories: Category[];
  created_at: string;
  updated_at: string;
}

export interface OdlNode {
  id: number;
  odl_node_id: string;
  bridge_name: string;
  dpid: string;
  device_name: string;
  device_ip: string;
}

export interface OdlController {
  id: number;
  type: "odl";
  device: Device;
  lan_ip_address: string;
}

export interface Category {
  id: number;
  name: string;
  category_cookie?: string;
}

export interface NetworkDevice {
  id: number;
  name: string;
  mac_address: string;
  ip_address?: string;
  device_type: string;
}

// --- ODL API Response Types ---
export interface OdlMeterApiResponse {
  results?: OdlMeter[];
  status?: string;
  message?: string;
}

export interface OdlNodeApiResponse {
  results?: OdlNode[];
  status?: string;
  message?: string;
}

export interface OdlControllerApiResponse {
  results?: OdlController[];
  status?: string;
  message?: string;
}

// --- ODL Meter Request/Response Types ---
export interface CreateOdlMeterRequest {
  controller_ip: string;
  switch_id: string;
  rate: number;
  categories: string[];
  model_name: string;
  mac_address?: string | null;
  activation_period: "all_week" | "weekday" | "weekend";
  start_time?: string | null;
  end_time?: string | null;
}

export interface UpdateOdlMeterRequest {
  controller_ip: string;
  switch_id: string;
  meter_id: number;
  rate: number;
  categories: string[];
  model_name: string;
  mac_address?: string | null;
  activation_period: "all_week" | "weekday" | "weekend";
  start_time?: string | null;
  end_time?: string | null;
}

export interface CreateOdlMeterResponse {
  status: "success" | "error";
  message: string;
  meter?: OdlMeter;
}

export interface UpdateOdlMeterResponse {
  status: "success" | "error";
  message: string;
  meter?: OdlMeter;
}

// --- Model Types ---
export interface ClassificationModel {
  name: string;
  display_name: string;
  model_type: string;
  num_categories: number;
  categories: string[];
  description: string;
  version: string;
  confidence_threshold: number;
  is_active: boolean;
  is_loaded: boolean;
  file_exists: boolean;
  input_shape: number[];
  category_count: number;
  meter_count: number;
}

export interface ModelInfo {
  models: ClassificationModel[];
  active_model: string;
  total_models: number;
}

export interface SetActiveModelRequest {
  model_name: string;
}

export interface SetActiveModelResponse {
  status: "success" | "error";
  message: string;
  active_model?: string;
}

// --- Category API Response Types ---
export interface CategoryApiResponse {
  categories: string[];
  active_model: string;
  total_categories: number;
  status?: string;
  message?: string;
}

// --- Model API Response Types ---
export interface ModelInfoApiResponse {
  status: "success" | "error";
  models: ClassificationModel[];
  active_model: string;
  total_models: number;
  message?: string;
}

// --- Network Device Search Types ---
export interface NetworkDeviceSearchResponse {
  results: NetworkDevice[];
  count: number;
  next?: string;
  previous?: string;
}

// --- Network Device API Types ---
export interface NetworkDeviceApiResponse {
  results: NetworkDevice[];
  count: number;
  next?: string;
  previous?: string;
}

// --- Historical Classification Data Types ---
export interface HistoricalClassificationData {
  [key: string]: number;
}

export interface HistoricalClassificationResponse {
  status: "success" | "error";
  message?: string;
  data?: HistoricalClassificationData;
}

export interface AggregatedClassificationDataPoint {
  name: string;
  count: number;
}

// --- Aggregated Data Per User Types ---
export interface AggregatedDataPerUserData {
  [macAddress: string]: number; // MAC address to total bytes mapping
}

export interface AggregatedDataPerUserResponse {
  status: "success" | "error";
  message?: string;
  data?: AggregatedDataPerUserData;
}

export interface AggregatedDataPerUserDataPoint {
  name: string; // MAC address
  megabytes: number;
}

export interface DeviceMetaData {
  [macAddress: string]: NetworkDeviceDetails;
}

// --- MAC Address Classification Data Types ---
export interface MacAddressClassificationData {
  [classification: string]: number;
}

export interface MacAddressClassificationResponse {
  status: "success" | "error";
  message?: string;
  data?: MacAddressClassificationData;
}

export interface MacAddressClassificationDataPoint {
  name: string; // classification name
  count: number;
}

// --- User Flow Data Types ---
export interface UserFlowData {
  [macAddress: string]: {
    [classification: string]: number; // classification to bytes mapping
  };
}

export interface UserFlowDataResponse {
  status: "success" | "error";
  message?: string;
  data?: UserFlowData;
}

export interface UserFlowDataPoint {
  name: string; // classification name
  megabytes: number;
}

// --- Data Per Classification Types ---
export interface DataPerClassificationData {
  [classification: string]: number; // classification to bytes mapping
}

export interface DataPerClassificationResponse {
  status: "success" | "error";
  message?: string;
  data?: DataPerClassificationData;
}

export interface DataPerClassificationDataPoint {
  name: string; // classification name
  megabytes: number;
}

export interface NetworkDeviceDetailResponse {
  id: number;
  name: string;
  mac_address: string;
  ip_address?: string;
  device_type: string;
  verified?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreateNetworkDeviceRequest {
  name: string;
  mac_address: string;
  ip_address?: string;
  device_type: string;
  verified?: boolean;
}

export interface UpdateNetworkDeviceRequest {
  name?: string;
  mac_address?: string;
  ip_address?: string;
  device_type?: string;
  verified?: boolean;
}

export interface NetworkDeviceFilters {
  id?: number;
  mac_address?: string;
  name?: string;
  device_type?: string;
  verified?: boolean;
  ip_address?: string;
}

export interface NetworkDeviceQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  id?: number;
  mac_address?: string;
  name?: string;
  device_type?: string;
  verified?: boolean;
  ip_address?: string;
}

// --- Alert Types ---
export interface AlertState {
  message: string;
  severity: "success" | "error" | "warning" | "info";
  show: boolean;
}

// --- Dialog State Types ---
export interface DialogState {
  isCreateDialogOpen: boolean;
  isCategoriesDialogOpen: boolean;
  isDeleteDialogOpen: boolean;
  currentNodeOdlId: string;
  currentMeter: OdlMeter | null;
  macAddress: string;
}

// --- Loading State Types ---
export interface LoadingState {
  isLoading: boolean;
  isLoadingNodes: boolean;
  isLoadingMeters: boolean;
}

// --- Page State Types ---
export interface TrafficClassificationState {
  controllers: OdlController[];
  selectedController: OdlController | null;
  nodes: OdlNode[];
  meters: OdlMeter[];
  categories: string[];
  alert: AlertState;
  dialog: DialogState;
  loading: LoadingState;
}

// --- Telegram Notification Types ---
export type NotificationType =
  | "Network Summary"
  | "Data Usage Alert"
  | "Application Usage Alert";

export interface TelegramNotification {
  id: number;
  type: NotificationType;
  frequency: number;
  top_users_count?: number;
  top_apps_count?: number;
  data_limit_mb?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTelegramNotificationRequest {
  type: NotificationType;
  frequency: number;
  top_users_count?: number;
  top_apps_count?: number;
  data_limit_mb?: number;
}

export interface UpdateTelegramNotificationRequest
  extends CreateTelegramNotificationRequest {
  id: number;
}

export interface TelegramNotificationApiResponse {
  status: "success" | "error";
  message?: string;
  data?: TelegramNotification[];
}

export interface TelegramNotificationState {
  notifications: TelegramNotification[];
  loading: boolean;
  error: string | null;
}

export interface UserProfile {
  telegram_username: string;
  phone_number: string;
  telegram_linked: boolean;
}

export interface UserData {
  user: {
    username: string;
    email: string;
  };
  profile: UserProfile;
}

// --- Account Settings Types ---
export interface AccountSettingsState {
  user: {
    username: string;
    email: string;
  };
  profile: UserProfile;
  isLoading: boolean;
  isEditing: boolean;
  isChangingPassword: boolean;
  isLinkingTelegram: boolean;
  error: string | null;
}

export interface ProfileFormData {
  username: string;
  email: string;
  telegram_username: string;
  phone_number: string;
}

export interface PasswordFormData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

export interface TelegramLinkData {
  unique_token: string;
  telegram_username?: string;
  phone_number?: string;
}

// --- User API Types ---
export interface UpdateUserProfileRequest {
  username?: string;
  email?: string;
  telegram_username?: string;
  phone_number?: string;
}

export interface UpdateUserProfileResponse {
  message: string;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
}

export interface LinkTelegramRequest {
  unique_token: string;
  telegram_username?: string;
  phone_number?: string;
}

export interface LinkTelegramResponse {
  message: string;
  telegram_linked: boolean;
}

export interface RefreshTokenResponse {
  token: string;
  expiry: string;
}

// Flexible translation types that automatically adapt to your locale structure
export type DeepNestedRecord = {
  [key: string]: string | DeepNestedRecord;
};

export type Translations = DeepNestedRecord;

// Type-safe translation access helper
export type TranslationPath<
  T,
  P extends string
> = P extends `${infer K}.${infer R}`
  ? K extends keyof T
    ? T[K] extends DeepNestedRecord
      ? TranslationPath<T[K], R>
      : never
    : never
  : P extends keyof T
  ? T[P]
  : never;

// --- WebSocket Message Types ---

// Device Stats WebSocket Messages
export interface DeviceStatsData {
  ip_address: string;
  cpu: number;
  memory: number;
  disk: number;
  timestamp?: string;
}

export interface DeviceStatsMessage {
  type: "stats";
  data: DeviceStatsData;
}

// OpenFlow WebSocket Messages
export interface OpenFlowMessage {
  type: "openflow";
  message: string;
}

// Flow WebSocket Messages
export interface FlowData {
  flow: Record<string, unknown>; // This can be expanded based on your flow data structure
}

export interface FlowMessage {
  type: "flow";
  flow: FlowData;
}

// Classification WebSocket Messages
export interface ClassificationData {
  classification: string;
  count: number;
  timestamp?: string;
  mac_address?: string;
  ip_address?: string;
}

export interface ClassificationMessage {
  type: "classification";
  data: ClassificationData;
}

// Union type for all WebSocket messages
export type WebSocketMessage =
  | DeviceStatsMessage
  | OpenFlowMessage
  | FlowMessage
  | ClassificationMessage;

// WebSocket connection types
export type WebSocketChannel = "deviceStats" | "openflow" | "classifications";

// Helper function for type-safe translation access with fallback
export function getTranslation<T extends DeepNestedRecord>(
  translations: T,
  path: string,
  fallback: string
): string {
  const keys = path.split(".");
  let current: DeepNestedRecord | string = translations;

  for (const key of keys) {
    if (current && typeof current === "object" && key in current) {
      current = current[key];
    } else {
      return fallback;
    }
  }

  return typeof current === "string" ? current : fallback;
}
