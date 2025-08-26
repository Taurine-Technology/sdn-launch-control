/*
 * File: ConnectionIndicator.tsx
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

import React, { useEffect, useState } from "react";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { useLanguage } from "@/context/languageContext";

interface ConnectionIndicatorProps {
  deviceIp: string;
  deviceType: string;
}

type ConnectionStatus = "checking" | "available" | "unavailable";

async function checkConnection(
  token: string,
  lanIpAddress: string,
  deviceType: string
) {
  const axiosInstance = (
    await import("@/lib/axiosInstance")
  ).createAxiosInstanceWithToken(token);
  const response = await axiosInstance.get(
    `/check-connection/${lanIpAddress}/${deviceType}/`
  );
  return response.data;
}

const ConnectionIndicator: React.FC<ConnectionIndicatorProps> = ({
  deviceIp,
  deviceType,
}) => {
  const { getT } = useLanguage();
  const [status, setStatus] = useState<ConnectionStatus>("checking");

  useEffect(() => {
    const checkDeviceConnection = async () => {
      if (!deviceIp || !deviceType) {
        setStatus("unavailable");
        return;
      }

      setStatus("checking");
      try {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("taurineToken") || ""
            : "";

        const response = await checkConnection(token, deviceIp, deviceType);

        // Check if the response indicates success
        if (response?.status === "success") {
          setStatus("available");
        } else {
          // Any non-success response (including error status) should show as unavailable
          setStatus("unavailable");
        }
      } catch (error) {
        // Any exception (network error, 500 error, etc.) should show as unavailable
        console.error("Connection check failed:", error);
        setStatus("unavailable");
      }
    };

    checkDeviceConnection();
  }, [deviceIp, deviceType]);

  const getStatusConfig = (status: ConnectionStatus) => {
    switch (status) {
      case "checking":
        return {
          color: "orange",
          label: getT("components.devices.connection_indicator.checking"),
        };
      case "available":
        return {
          color: "green",
          label: getT(
            "components.devices.connection_indicator.device_available"
          ),
        };
      case "unavailable":
        return {
          color: "red",
          label: getT(
            "components.devices.connection_indicator.device_unavailable"
          ),
        };
      default:
        return {
          color: "red",
          label: getT(
            "components.devices.connection_indicator.device_unavailable"
          ),
        };
    }
  };

  const { color, label } = getStatusConfig(status);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span
          className="inline-block w-4 h-4 rounded-full border border-black cursor-pointer"
          style={{ backgroundColor: color }}
        />
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
};

export default ConnectionIndicator;
