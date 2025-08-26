/*
 * File: CreateMeterDialog.tsx
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

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";

import { odlCreateMeter, searchNetworkDevices } from "@/lib/odl";
import { CreateOdlMeterRequest, NetworkDevice } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";
import { useModel } from "@/context/ModelContext";

interface CreateMeterDialogProps {
  open: boolean;
  onClose: (success: boolean) => void;
  controllerIP: string;
  switchNodeId: string;
  categories: string[];
  selectedModel?: string;
}

export const CreateMeterDialog: React.FC<CreateMeterDialogProps> = ({
  open,
  onClose,
  controllerIP,
  switchNodeId,
  categories,
  selectedModel,
}) => {
  const { getT } = useLanguage();
  const { activeModel } = useModel();
  const [rate, setRate] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedDeviceMac, setSelectedDeviceMac] = useState("");
  const [selectedDevice, setSelectedDevice] = useState<NetworkDevice | null>(
    null
  );
  const [networkDevices, setNetworkDevices] = useState<NetworkDevice[]>([]);
  const [deviceSearch, setDeviceSearch] = useState("");
  const [isSearchingDevices, setIsSearchingDevices] = useState(false);
  const [activationPeriod, setActivationPeriod] = useState<
    "all_week" | "weekday" | "weekend"
  >("all_week");
  const [isLoading, setIsLoading] = useState(false);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [currentModel, setCurrentModel] = useState<string>("");

  const resetForm = () => {
    setRate("");
    setSelectedCategories([]);
    setSelectedDeviceMac("");
    setSelectedDevice(null);
    setDeviceSearch("");
    setActivationPeriod("all_week");
    setStartTime("");
    setEndTime("");
    setCurrentModel(selectedModel || activeModel?.name || "");
  };

  const handleDeviceSelect = (device: NetworkDevice) => {
    setSelectedDeviceMac(device.mac_address);
    setSelectedDevice(device); // Store the full device object
    setDeviceSearch(""); // Reset search
    setNetworkDevices([]); // Clear dropdown
  };

  const handleRemoveDevice = () => {
    setSelectedDeviceMac("");
    setSelectedDevice(null);
    setNetworkDevices([]); // Clear dropdown
  };

  const handleSearchChange = (value: string) => {
    setDeviceSearch(value);
    if (!value) {
      setNetworkDevices([]); // Clear dropdown when search is empty
    }
  };

  // Debounced search function for devices
  const searchDevices = async (searchTerm: string) => {
    if (!searchTerm || searchTerm.trim().length < 2) {
      setNetworkDevices([]);
      return;
    }

    setIsSearchingDevices(true);
    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) throw new Error("No token found");

      const response = await searchNetworkDevices(token, searchTerm.trim(), 20);
      setNetworkDevices(response.results || []);
    } catch (error) {
      console.error("Failed to search network devices:", error);
      setNetworkDevices([]);
    } finally {
      setIsSearchingDevices(false);
    }
  };

  // Initialize current model when dialog opens
  useEffect(() => {
    if (open) {
      setCurrentModel(selectedModel || activeModel?.name || "");
    }
  }, [open, selectedModel, activeModel]);

  // Debounce search with useEffect
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (deviceSearch) {
        searchDevices(deviceSearch);
      } else {
        setNetworkDevices([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [deviceSearch]);

  const handleSubmit = async () => {
    if (!rate) {
      toast.error(getT("components.meters.create_meter_dialog.rate_required"));
      return;
    }

    const rateValue = parseInt(rate, 10);
    if (isNaN(rateValue) || rateValue <= 0) {
      toast.error(
        getT("components.meters.create_meter_dialog.rate_positive_number")
      );
      return;
    }

    setIsLoading(true);

    const token = localStorage.getItem("taurineToken");
    if (!token) {
      toast.error(
        getT("components.meters.create_meter_dialog.auth_token_not_found")
      );
      setIsLoading(false);
      return;
    }

    const payload: CreateOdlMeterRequest = {
      controller_ip: controllerIP,
      switch_id: switchNodeId,
      rate: rateValue,
      categories: selectedCategories,
      model_name: currentModel,
      mac_address: selectedDeviceMac || null,
      activation_period: activationPeriod,
      start_time: startTime || null,
      end_time: endTime || null,
    };

    console.log("[ Meter Creation Dialog ] payload is:", payload);

    try {
      await odlCreateMeter(token, payload);
      toast.success(getT("components.meters.create_meter_dialog.success"));
      resetForm();
      onClose(true);
    } catch (error: unknown) {
      const errMsg =
        error instanceof Error
          ? error.message
          : getT("components.meters.create_meter_dialog.error");
      toast.error(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryChange = (category: string, checked: boolean) => {
    if (checked) {
      setSelectedCategories((prev) => [...prev, category]);
    } else {
      setSelectedCategories((prev) => prev.filter((c) => c !== category));
    }
  };

  const handleSelectAllCategories = () => {
    setSelectedCategories(categories);
  };

  const handleClearCategories = () => {
    setSelectedCategories([]);
  };

  const handleCloseDialog = () => {
    if (!isLoading) {
      resetForm();
      onClose(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleCloseDialog}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>
            {getT("components.meters.create_meter_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.meters.create_meter_dialog.description")}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Model Information */}
          {currentModel && (
            <div className="grid gap-2">
              <Label>
                {getT(
                  "components.meters.create_meter_dialog.model_info",
                  "Model Information"
                )}
              </Label>
              <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                <Badge variant="outline" className="text-sm">
                  {getT(
                    "components.meters.create_meter_dialog.active_model",
                    "Active Model"
                  )}
                  :
                </Badge>
                <span className="text-sm font-medium">{currentModel}</span>
                {activeModel && (
                  <span className="text-xs text-muted-foreground">
                    ({activeModel.num_categories} categories)
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="grid gap-2">
            <Label htmlFor="rate">
              {getT("components.meters.create_meter_dialog.rate")}
            </Label>
            <Input
              id="rate"
              type="number"
              min="1"
              step="1"
              value={rate}
              onChange={(e) => {
                const value = e.target.value;
                if (value === "" || parseInt(value, 10) > 0) {
                  setRate(value);
                }
              }}
              placeholder={getT(
                "components.meters.create_meter_dialog.rate_placeholder"
              )}
            />
            {rate !== "" &&
              (isNaN(parseInt(rate, 10)) || parseInt(rate, 10) <= 0) && (
                <p className="text-sm text-destructive">
                  {getT(
                    "components.meters.create_meter_dialog.rate_positive_number"
                  )}
                </p>
              )}
          </div>

          <div className="grid gap-2">
            <Label>
              {getT("components.meters.create_meter_dialog.categories")}
            </Label>
            <div className="flex gap-2 mb-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleSelectAllCategories}
              >
                {getT("components.meters.create_meter_dialog.select_all")}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleClearCategories}
              >
                {getT("components.meters.create_meter_dialog.clear_all")}
              </Button>
            </div>
            <ScrollArea className="h-[120px] w-full rounded-md border p-4">
              <div className="grid grid-cols-2 gap-2">
                {categories.length === 0 ? (
                  <div className="col-span-2 text-center text-muted-foreground text-sm py-4">
                    No categories available.
                  </div>
                ) : (
                  categories.map((category) => (
                    <div key={category} className="flex items-center space-x-2">
                      <Checkbox
                        id={category}
                        checked={selectedCategories.includes(category)}
                        onCheckedChange={(checked) =>
                          handleCategoryChange(category, checked as boolean)
                        }
                      />
                      <Label htmlFor={category} className="text-sm">
                        {category}
                      </Label>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
            {selectedCategories.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {selectedCategories.map((category) => (
                  <Badge key={category} variant="secondary">
                    {category}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="grid gap-2">
            <Label>
              {getT("components.meters.create_meter_dialog.network_device")}
            </Label>
            <Input
              placeholder={getT(
                "components.meters.create_meter_dialog.network_device_placeholder"
              )}
              value={deviceSearch}
              onChange={(e) => handleSearchChange(e.target.value)}
            />
            {isSearchingDevices && (
              <p className="text-sm text-muted-foreground">
                {getT("components.meters.create_meter_dialog.searching")}
              </p>
            )}
            {networkDevices.length > 0 && (
              <ScrollArea className="h-[100px] w-full rounded-md border p-2">
                <div className="space-y-1">
                  {networkDevices.map((device) => (
                    <div
                      key={device.mac_address}
                      className={`p-2 rounded cursor-pointer hover:bg-accent ${
                        selectedDeviceMac === device.mac_address
                          ? "bg-accent"
                          : ""
                      }`}
                      onClick={() => handleDeviceSelect(device)}
                    >
                      <div className="font-medium">
                        {device.name ||
                          device.ip_address ||
                          device.mac_address ||
                          getT(
                            "components.meters.create_meter_dialog.unnamed_device"
                          )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {device.ip_address && `IP: ${device.ip_address}`}
                        {device.ip_address && device.mac_address && " | "}
                        {device.mac_address && `MAC: ${device.mac_address}`}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
            {selectedDevice && (
              <div className="p-3 bg-accent rounded border">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-sm">
                      {selectedDevice.name ||
                        getT(
                          "components.meters.create_meter_dialog.unnamed_device"
                        )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      MAC: {selectedDevice.mac_address}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRemoveDevice}
                    className="h-6 w-6 p-0"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-3 w-3"
                    >
                      <path d="M18 6L6 18" />
                      <path d="M6 6L18 18" />
                    </svg>
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="activation-period">
              {getT("components.meters.create_meter_dialog.activation_period")}
            </Label>
            <Select
              value={activationPeriod}
              onValueChange={(value: "all_week" | "weekday" | "weekend") =>
                setActivationPeriod(value)
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all_week">
                  {getT("components.meters.create_meter_dialog.all_week")}
                </SelectItem>
                <SelectItem value="weekday">
                  {getT("components.meters.create_meter_dialog.weekday_only")}
                </SelectItem>
                <SelectItem value="weekend">
                  {getT("components.meters.create_meter_dialog.weekend_only")}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="start-time">
                {getT("components.meters.create_meter_dialog.start_time")}
              </Label>
              <Input
                id="start-time"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="[&::-webkit-calendar-picker-indicator]:invert"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="end-time">
                {getT("components.meters.create_meter_dialog.end_time")}
              </Label>
              <Input
                id="end-time"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="[&::-webkit-calendar-picker-indicator]:invert"
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCloseDialog}
            disabled={isLoading}
          >
            {getT("components.meters.create_meter_dialog.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isLoading || selectedCategories.length < 1 || !rate}
          >
            {isLoading
              ? getT("components.meters.create_meter_dialog.creating")
              : getT("components.meters.create_meter_dialog.create")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
