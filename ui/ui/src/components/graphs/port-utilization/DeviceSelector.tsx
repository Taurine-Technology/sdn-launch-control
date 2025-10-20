/*
 * File: DeviceSelector.tsx
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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLanguage } from "@/context/languageContext";
import { DevicePortData } from "@/lib/types";

interface DeviceSelectorProps {
  devices: DevicePortData[];
  selectedDevice: string;
  onChange: (deviceIp: string) => void;
}

export function DeviceSelector({
  devices,
  selectedDevice,
  onChange,
}: DeviceSelectorProps) {
  const { getT } = useLanguage();

  return (
    <Select value={selectedDevice} onValueChange={onChange}>
      <SelectTrigger className="w-[250px]">
        <SelectValue
          placeholder={getT(
            "page.PortUtilizationPage.select_device_placeholder",
            "Choose a device"
          )}
        />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">
          {getT("page.PortUtilizationPage.all_devices", "All Devices")}
        </SelectItem>
        {devices.map((device) => (
          <SelectItem key={device.ip_address} value={device.ip_address}>
            {device.ip_address}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
