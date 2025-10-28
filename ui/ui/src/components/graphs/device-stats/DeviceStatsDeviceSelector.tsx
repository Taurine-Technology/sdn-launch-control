/**
 * File: DeviceStatsDeviceSelector.tsx
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
import { NetworkDeviceDetails } from "@/lib/types";

interface Props {
  devices: NetworkDeviceDetails[];
  selectedIp: string;
  onChange: (ip: string) => void;
}

export function DeviceStatsDeviceSelector({
  devices,
  selectedIp,
  onChange,
}: Props) {
  const { getT } = useLanguage();

  return (
    <Select value={selectedIp} onValueChange={onChange}>
      <SelectTrigger className="w-[280px]">
        <SelectValue
          placeholder={getT(
            "page.DeviceStatsPage.select_device",
            "Select device"
          )}
        />
      </SelectTrigger>
      <SelectContent>
        {devices.map((d) => {
          const ip = (d.lan_ip_address as string) || d.ip_address || "";
          return (
            <SelectItem key={d.id} value={ip}>
              {d.name ? `${d.name} (${ip})` : ip}
            </SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  );
}
