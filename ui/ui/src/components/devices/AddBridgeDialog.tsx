/*
 * File: AddBridgeDialog.tsx
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

import React, { useEffect, useState, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RingLoader } from "react-spinners";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { MultiSelect, MultiSelectBadges } from "@/components/ui/multi-select";
import { Controller, Bridge } from "@/lib/types";
import {
  addBridge,
  fetchControllers,
  fetchUnassignedPorts,
  installQosMonitoring,
} from "@/lib/devices";
import { validateApiUrl } from "@/lib/utils";
import { useLanguage } from "@/context/languageContext";

interface AddBridgeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  deviceIp: string;
  onBridgeAdded: () => void;
  onBridgeSuccess: (message: string) => void;
  onBridgeError: (message: string) => void;
  onQosSuccess: (message: string) => void;
  onQosError: (message: string) => void;
}

interface PortOption {
  id: string;
  name: string;
}

interface BridgePayload {
  lan_ip_address: string;
  name: string;
  openFlowVersion: string;
  ports: string[];
  api_url: string;
  controller_ip?: string;
  controller_port?: string;
}

const AddBridgeDialog: React.FC<AddBridgeDialogProps> = ({
  isOpen,
  onClose,
  deviceIp,
  onBridgeAdded,
  onBridgeSuccess,
  onBridgeError,
  onQosSuccess,
  onQosError,
}) => {
  const { getT } = useLanguage();
  const [bridgeName, setBridgeName] = useState("");
  const [bridgeNameError, setBridgeNameError] = useState("");
  const [openFlowVersion, setOpenFlowVersion] = useState("1.3");
  const [selectedPorts, setSelectedPorts] = useState<string[]>([]);
  const [portOptions, setPortOptions] = useState<PortOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [controllers, setControllers] = useState<Controller[]>([]);
  const [selectedController, setSelectedController] = useState("");
  const [controllerPort, setControllerPort] = useState("6653");
  const [apiUrl, setApiUrl] = useState("");
  const [apiUrlError, setApiUrlError] = useState("");

  const validateBridgeName = (name: string): string => {
    if (!name.trim()) {
      return "";
    }
    const regex = /^[a-zA-Z0-9-]+$/;
    if (!regex.test(name)) {
      return "No spaces or special characters allowed, except hyphens (-).";
    }
    return ""; // No error
  };

  const handleBridgeNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value;
    setBridgeName(newName);
    setBridgeNameError(validateBridgeName(newName));
  };

  const handleApiUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value;
    setApiUrl(newUrl);
    setApiUrlError(validateApiUrl(newUrl));
  };

  const resetForm = () => {
    setBridgeName("");
    setBridgeNameError("");
    setApiUrl("");
    setApiUrlError("");
    setSelectedPorts([]);
    setSelectedController("");
    setControllerPort("6653");
    setOpenFlowVersion("1.3");
  };

  const handleClose = () => {
    if (!isLoading) {
      resetForm();
      onClose();
    }
  };

  const fetchPorts = useCallback(async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem("taurineToken") || "";
      const data = await fetchUnassignedPorts(token, deviceIp);

      if (data.status === "success") {
        setPortOptions(
          data.interfaces && data.interfaces.length > 0
            ? data.interfaces.map((port: string) => ({ id: port, name: port }))
            : []
        );
      } else {
        setPortOptions([]);
      }
    } catch (error) {
      console.error("Error fetching ports:", error);
      setPortOptions([]);
      onBridgeError("Failed to fetch ports.");
    } finally {
      setIsLoading(false);
    }
  }, [deviceIp, onBridgeError]);

  const getControllers = useCallback(async () => {
    try {
      const token = localStorage.getItem("taurineToken") || "";
      const response = await fetchControllers(token);
      // console.log("[ADDBRIDGEDIALOG.tsx] controllers", response);
      setControllers(response || []);
    } catch (error) {
      console.error("Error fetching controllers:", error);
      setControllers([]);
      onBridgeError("Failed to fetch controllers.");
    }
  }, [onBridgeError]);

  useEffect(() => {
    if (isOpen) {
      fetchPorts();
      getControllers();
    }
  }, [isOpen, deviceIp, fetchPorts, getControllers]);

  // Separate effects for validation
  useEffect(() => {
    if (isOpen) {
      setBridgeNameError(validateBridgeName(bridgeName));
    }
  }, [bridgeName, isOpen]);

  useEffect(() => {
    if (isOpen) {
      setApiUrlError(validateApiUrl(apiUrl));
    }
  }, [apiUrl, isOpen]);

  const handleSubmit = async () => {
    const currentBridgeNameError = validateBridgeName(bridgeName);
    if (currentBridgeNameError) {
      setBridgeNameError(currentBridgeNameError);
      return;
    }
    if (!apiUrl.trim()) {
      onBridgeError("API URL is required.");
      return;
    }

    setIsLoading(true);
    let payload: BridgePayload = {
      lan_ip_address: deviceIp,
      name: bridgeName,
      openFlowVersion: openFlowVersion,
      ports: selectedPorts,
      api_url: apiUrl,
    };

    if (selectedController) {
      payload = {
        ...payload,
        controller_ip: selectedController,
        controller_port: controllerPort,
      };
    }

    try {
      const token = localStorage.getItem("taurineToken") || "";
      await addBridge(token, payload as unknown as Partial<Bridge>);

      onBridgeSuccess("Bridge added successfully... Adding QoS monitor");

      try {
        await installQosMonitoring(
          token,
          payload as unknown as Record<string, unknown>
        );
        onQosSuccess("Bridge and QoS monitor added successfully");
      } catch (qosError) {
        console.error("QoS installation failed:", qosError);
        onQosError("Bridge added but QoS monitor installation failed");
      }

      resetForm();
      onBridgeAdded(); // Refresh bridge data
    } catch (error) {
      console.error("Error adding bridge:", error);
      onBridgeError("Error adding bridge. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handlePortChange = (values: string[]) => {
    setSelectedPorts(values);
  };

  const handlePortRemove = (value: string) => {
    setSelectedPorts(selectedPorts.filter((port) => port !== value));
  };

  const isSubmitDisabled =
    isLoading ||
    !bridgeName ||
    !!bridgeNameError ||
    !apiUrl ||
    !!apiUrlError ||
    selectedPorts.length === 0;

  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (!open && !isLoading) {
          handleClose();
        }
      }}
      modal={true}
    >
      <DialogContent
        onInteractOutside={isLoading ? (e) => e.preventDefault() : undefined}
        onEscapeKeyDown={isLoading ? (e) => e.preventDefault() : undefined}
        onPointerDownOutside={isLoading ? (e) => e.preventDefault() : undefined}
        className="sm:max-w-[600px]"
      >
        {isLoading && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80">
            <RingLoader color="#7456FD" size={60} />
          </div>
        )}
        <DialogHeader>
          <DialogTitle>
            {getT("components.devices.add_bridge_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.devices.add_bridge_dialog.description")}
          </DialogDescription>
        </DialogHeader>
        <div
          className={`flex flex-col gap-4 mt-2 ${
            isLoading ? "pointer-events-none opacity-60" : ""
          }`}
        >
          <div className="grid gap-2">
            <Label htmlFor="bridge-name">
              {getT("components.devices.add_bridge_dialog.bridge_name")}
            </Label>
            <Input
              id="bridge-name"
              placeholder={getT(
                "components.devices.add_bridge_dialog.bridge_name_placeholder"
              )}
              value={bridgeName}
              onChange={handleBridgeNameChange}
              disabled={isLoading}
              required
            />
            {bridgeNameError && (
              <span className="text-red-500 text-xs">{bridgeNameError}</span>
            )}
            <span className="text-xs text-muted-foreground">
              {getT("components.devices.add_bridge_dialog.bridge_name_help")}
            </span>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="api-url">
              {getT("components.devices.add_bridge_dialog.api_url")}
            </Label>
            <Input
              id="api-url"
              placeholder={getT(
                "components.devices.add_bridge_dialog.api_url_placeholder"
              )}
              value={apiUrl}
              onChange={handleApiUrlChange}
              disabled={isLoading}
              required
            />
            {apiUrlError && (
              <span className="text-red-500 text-xs">{apiUrlError}</span>
            )}
            <span className="text-xs text-muted-foreground">
              {getT("components.devices.add_bridge_dialog.api_url_help")}
            </span>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="openflow-version">
              {getT("components.devices.add_bridge_dialog.openflow_version")}
            </Label>
            <Select
              value={openFlowVersion}
              onValueChange={setOpenFlowVersion}
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={getT(
                    "components.devices.add_bridge_dialog.openflow_version_placeholder"
                  )}
                />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1.3">1.3</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="ports">
              {getT("components.devices.add_bridge_dialog.ports")}
            </Label>
            <MultiSelect
              options={portOptions.map((port) => ({
                value: port.name,
                label: port.name,
              }))}
              selectedValues={selectedPorts}
              onSelectionChange={handlePortChange}
              placeholder={getT(
                "components.devices.add_bridge_dialog.ports_placeholder"
              )}
              searchPlaceholder={getT(
                "components.devices.add_bridge_dialog.ports_search_placeholder"
              )}
              emptyMessage={getT(
                "components.devices.add_bridge_dialog.ports_empty_message"
              )}
              disabled={isLoading}
            />
            <MultiSelectBadges
              selectedValues={selectedPorts}
              options={portOptions.map((port) => ({
                value: port.name,
                label: port.name,
              }))}
              onRemove={handlePortRemove}
            />
          </div>
          {controllers.length > 0 && (
            <div className="grid gap-2">
              <Label htmlFor="controller">
                {getT("components.devices.add_bridge_dialog.controller")}
              </Label>
              <Select
                value={selectedController}
                onValueChange={(value) => {
                  setSelectedController(value);
                  setControllerPort(value ? "6653" : "");
                }}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={getT(
                      "components.devices.add_bridge_dialog.controller_placeholder"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {controllers.map((controller) => (
                    <SelectItem
                      key={controller.id}
                      value={controller.lan_ip_address || ""}
                    >
                      {controller.lan_ip_address}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {controllers.length > 0 && selectedController && (
            <div className="grid gap-2">
              <Label htmlFor="controller-port">
                {getT("components.devices.add_bridge_dialog.controller_port")}
              </Label>
              <Input
                id="controller-port"
                placeholder={getT(
                  "components.devices.add_bridge_dialog.controller_port_placeholder"
                )}
                value={controllerPort}
                onChange={(e) => setControllerPort(e.target.value)}
                disabled={isLoading}
                required
              />
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            {getT("components.devices.add_bridge_dialog.cancel")}
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitDisabled}>
            {isLoading
              ? getT("components.devices.add_bridge_dialog.adding")
              : getT("components.devices.add_bridge_dialog.add")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AddBridgeDialog;
