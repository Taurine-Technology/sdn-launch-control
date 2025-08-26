"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Download } from "lucide-react";
import {
  NetworkDeviceDetails,
  Bridge,
  Port,
  PluginInstallation,
} from "@/lib/types";
import { installSniffer } from "@/lib/software";
import { toast } from "sonner";
import { fetchBridges } from "@/lib/devices";
import { validateApiUrl } from "@/lib/utils";
import { RingLoader } from "react-spinners";
import { useLanguage } from "@/context/languageContext";

interface SnifferInstallFormProps {
  devices: NetworkDeviceDetails[];
  installations: PluginInstallation[];
  onInstallSuccess: () => void;
}

export function SnifferInstallForm({
  devices,
  installations,
  onInstallSuccess,
}: SnifferInstallFormProps) {
  const { getT } = useLanguage();
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Filter out devices that already have sniffer installations
  const availableDevices = devices.filter((device) => {
    return !installations.some((installation) => {
      return (
        installation.plugin?.name === "tau-traffic-classification-sniffer" &&
        installation.device?.lan_ip_address === device.lan_ip_address
      );
    });
  });

  // Check if any devices are available for installation
  const hasAvailableDevices = availableDevices.length > 0;

  // Form state
  const [selectedDevice, setSelectedDevice] =
    useState<NetworkDeviceDetails | null>(null);
  const [apiUrl, setApiUrl] = useState("");
  const [selectedBridge, setSelectedBridge] = useState("");
  const [monitoringInterface, setMonitoringInterface] = useState("");
  const [clientPort, setClientPort] = useState("");
  const [wanPort, setWanPort] = useState("");

  // Data state
  const [deviceBridges, setDeviceBridges] = useState<Bridge[]>([]);
  const [bridgePorts, setBridgePorts] = useState<Port[]>([]);
  const [bridgesLoading, setBridgesLoading] = useState(false);

  // Error state
  const [portSelectionError, setPortSelectionError] = useState("");
  const [apiUrlError, setApiUrlError] = useState("");

  // Form validation
  const isFormValid =
    selectedDevice &&
    apiUrl.trim() &&
    !apiUrlError &&
    selectedBridge &&
    monitoringInterface &&
    clientPort &&
    wanPort &&
    clientPort !== wanPort;

  // Fetch bridges when device changes
  useEffect(() => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("taurineToken") || ""
        : "";
    if (!selectedDevice || !token) {
      setDeviceBridges([]);
      setSelectedBridge("");
      setBridgePorts([]);
      setMonitoringInterface("");
      setClientPort("");
      setWanPort("");
      return;
    }

    const fetchData = async () => {
      setBridgesLoading(true);
      try {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("taurineToken") || ""
            : "";
        const data = await fetchBridges(token, selectedDevice.id.toString());
        setDeviceBridges(data.bridges as Bridge[]);
      } catch (err) {
        console.error("Error fetching bridges:", err);
        toast.error("Failed to fetch bridges");
        setDeviceBridges([]);
      } finally {
        setBridgesLoading(false);
      }
    };

    fetchData();
  }, [selectedDevice]);

  // Update ports when bridge changes
  useEffect(() => {
    if (!selectedBridge) {
      setBridgePorts([]);
      setMonitoringInterface("");
      setClientPort("");
      setWanPort("");
      return;
    }

    // Find the selected bridge and get its ports
    const selectedBridgeData = deviceBridges.find(
      (bridge) => bridge.id.toString() === selectedBridge
    );

    if (selectedBridgeData) {
      setBridgePorts(selectedBridgeData.ports);
    } else {
      setBridgePorts([]);
    }

    // Reset port selections
    setMonitoringInterface("");
    setClientPort("");
    setWanPort("");
  }, [selectedBridge, deviceBridges]);

  // Validate port selection
  useEffect(() => {
    if (clientPort && wanPort && clientPort === wanPort) {
      setPortSelectionError(
        getT("components.plugins.sniffer_install_form.port_selection_error")
      );
    } else {
      setPortSelectionError("");
    }
  }, [clientPort, wanPort, getT]);

  // Validate API URL
  useEffect(() => {
    const error = validateApiUrl(apiUrl);
    setApiUrlError(error);
  }, [apiUrl]);

  const handleSubmit = async () => {
    if (!isFormValid) return;

    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("taurineToken") || ""
        : "";

    if (!token) {
      toast.error(
        getT("components.plugins.sniffer_install_form.auth_token_not_found")
      );
      return;
    }

    setIsLoading(true);

    // Get the bridge name from the selected bridge ID
    const selectedBridgeData = deviceBridges.find(
      (bridge) => bridge.id.toString() === selectedBridge
    );
    const bridgeName = selectedBridgeData?.name || "";

    const payload = {
      lan_ip_address: selectedDevice.lan_ip_address || "",
      api_base_url: apiUrl,
      monitor_interface: monitoringInterface,
      port_to_client: clientPort,
      port_to_router: wanPort,
      bridge_name: bridgeName,
    };

    try {
      await installSniffer(token, payload);
      toast.success(
        getT("components.plugins.sniffer_install_form.install_success")
      );
      onInstallSuccess();
      setOpen(false);
      // Reset form
      setSelectedDevice(null);
      setApiUrl("");
      setSelectedBridge("");
      setMonitoringInterface("");
      setClientPort("");
      setWanPort("");
    } catch (err) {
      console.error("Error installing sniffer:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : getT("components.plugins.sniffer_install_form.install_error");
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (isLoading) return;
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm" className="flex-1" disabled={!hasAvailableDevices}>
          {hasAvailableDevices ? (
            <>
              <Download className="w-4 h-4 mr-2" />
              {getT("components.plugins.sniffer_install_form.install")}
            </>
          ) : (
            getT("components.plugins.sniffer_install_form.no_available_device")
          )}
        </Button>
      </DialogTrigger>
      <DialogContent
        className="sm:max-w-[500px]"
        onInteractOutside={isLoading ? (e) => e.preventDefault() : undefined}
        onEscapeKeyDown={isLoading ? (e) => e.preventDefault() : undefined}
        onPointerDownOutside={isLoading ? (e) => e.preventDefault() : undefined}
      >
        {isLoading && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80">
            <RingLoader color="#7456FD" size={60} />
          </div>
        )}
        <DialogHeader>
          <DialogTitle>
            {getT("components.plugins.sniffer_install_form.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.plugins.sniffer_install_form.description")}
          </DialogDescription>
        </DialogHeader>

        {!hasAvailableDevices ? (
          <div className="py-8 text-center">
            <p className="text-muted-foreground mb-4">
              {getT(
                "components.plugins.sniffer_install_form.all_devices_installed"
              )}
            </p>
            <p className="text-sm text-muted-foreground">
              {getT(
                "components.plugins.sniffer_install_form.add_new_device_message"
              )}
            </p>
          </div>
        ) : (
          <div
            className={`grid gap-4 py-4 ${
              isLoading ? "pointer-events-none opacity-60" : ""
            }`}
          >
            {/* Device Selection */}
            <div className="grid gap-2">
              <Label htmlFor="device">
                {getT("components.plugins.sniffer_install_form.select_device")}
              </Label>
              <Select
                value={selectedDevice?.lan_ip_address || ""}
                onValueChange={(value) =>
                  setSelectedDevice(
                    availableDevices.find((d) => d.lan_ip_address === value) ||
                      null
                  )
                }
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={getT(
                      "components.plugins.sniffer_install_form.choose_device"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {availableDevices.map((device) => (
                    <SelectItem
                      key={`device-${device.lan_ip_address}`}
                      value={device.lan_ip_address || ""}
                    >
                      {device.name} ({device.lan_ip_address})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Bridge Selection */}
            <div className="grid gap-2">
              <Label htmlFor="bridge">
                {getT("components.plugins.sniffer_install_form.select_bridge")}
              </Label>
              <Select
                value={selectedBridge}
                onValueChange={setSelectedBridge}
                disabled={bridgesLoading || !selectedDevice || isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={
                      bridgesLoading
                        ? getT(
                            "components.plugins.sniffer_install_form.loading_bridges"
                          )
                        : getT(
                            "components.plugins.sniffer_install_form.choose_bridge"
                          )
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {deviceBridges.map((bridge) => (
                    <SelectItem
                      key={`bridge-${bridge.id}`}
                      value={bridge.id.toString()}
                    >
                      {bridge.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* API URL */}
            <div className="grid gap-2">
              <Label htmlFor="apiUrl">
                {getT("components.plugins.sniffer_install_form.api_url")}
              </Label>
              <Input
                id="apiUrl"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                placeholder={getT(
                  "components.plugins.sniffer_install_form.api_url_placeholder"
                )}
                disabled={isLoading}
              />
              {apiUrlError && (
                <p className="text-sm text-destructive">{apiUrlError}</p>
              )}
            </div>

            {/* Monitoring Interface */}
            <div className="grid gap-2">
              <Label htmlFor="monitoring">
                {getT(
                  "components.plugins.sniffer_install_form.monitoring_interface"
                )}
              </Label>
              <Select
                value={monitoringInterface}
                onValueChange={setMonitoringInterface}
                disabled={!selectedBridge || isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={getT(
                      "components.plugins.sniffer_install_form.choose_monitoring_port"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {bridgePorts.map((port) => (
                    <SelectItem
                      key={`monitor-port-${port.id}`}
                      value={port.name}
                    >
                      {port.name} (OVS Port: {port.ovs_port_number})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Client Port */}
            <div className="grid gap-2">
              <Label htmlFor="clientPort">
                {getT("components.plugins.sniffer_install_form.client_port")}
              </Label>
              <Select
                value={clientPort}
                onValueChange={setClientPort}
                disabled={!selectedBridge || isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={getT(
                      "components.plugins.sniffer_install_form.choose_client_port"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {bridgePorts
                    .filter((port) => port.ovs_port_number != null)
                    .map((port) => (
                      <SelectItem
                        key={`client-port-${port.id}`}
                        value={port.ovs_port_number!.toString()}
                      >
                        {port.name} (OVS Port: {port.ovs_port_number})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {/* WAN Port */}
            <div className="grid gap-2">
              <Label htmlFor="wanPort">
                {getT("components.plugins.sniffer_install_form.wan_port")}
              </Label>
              <Select
                value={wanPort}
                onValueChange={setWanPort}
                disabled={!selectedBridge || isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={getT(
                      "components.plugins.sniffer_install_form.choose_wan_port"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {bridgePorts
                    .filter((port) => port.ovs_port_number != null)
                    .map((port) => (
                      <SelectItem
                        key={`wan-port-${port.id}`}
                        value={port.ovs_port_number!.toString()}
                      >
                        {port.name} (OVS Port: {port.ovs_port_number})
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            {portSelectionError && (
              <div className="text-sm text-destructive">
                {portSelectionError}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            {hasAvailableDevices
              ? getT("components.plugins.sniffer_install_form.cancel")
              : getT("components.plugins.sniffer_install_form.close")}
          </Button>
          {hasAvailableDevices && (
            <Button onClick={handleSubmit} disabled={isLoading || !isFormValid}>
              {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isLoading
                ? getT("components.plugins.sniffer_install_form.installing")
                : getT("components.plugins.sniffer_install_form.install")}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
