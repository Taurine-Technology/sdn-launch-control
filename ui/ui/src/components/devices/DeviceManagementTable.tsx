"use client";

import * as React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Monitor, Search, Wifi, WifiOff, Plus } from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";
import { fetchDeviceUptimeStatus } from "@/lib/deviceMonitoring";
import { createAxiosInstanceWithToken } from "@/lib/axiosInstance";
import { DeviceUptimeStatus } from "@/lib/types";
import RingLoader from "react-spinners/RingLoader";
import AddDeviceDialog from "./AddDeviceDialog";

interface DeviceManagementTableProps {
  onToggleMonitoring: (deviceId: number, enable: boolean) => Promise<void>;
}

const DeviceManagementTable: React.FC<DeviceManagementTableProps> = ({
  onToggleMonitoring,
}) => {
  const { getT } = useLanguage();
  const { token } = useAuth();
  const [devices, setDevices] = React.useState<DeviceUptimeStatus[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [toggling, setToggling] = React.useState<number | null>(null);
  const [showAddDialog, setShowAddDialog] = React.useState(false);

  const loadDevices = React.useCallback(async () => {
    if (!token) return;

    setLoading(true);
    try {
      // Fetch uptime status for devices that have been pinged
      const uptimeData = await fetchDeviceUptimeStatus(token, "24 hours");

      // Create a map of device_id -> uptime data
      const uptimeMap = new Map(uptimeData.map((d) => [d.device_id, d]));

      // Fetch all network devices (paginated, so get first page with large size)
      const axiosInstance = createAxiosInstanceWithToken(token);
      const { data: allDevicesResponse } = await axiosInstance.get(
        "/network-devices/?page_size=200"
      );
      const allDevices = allDevicesResponse.results || allDevicesResponse;

      // Merge: for each device, add uptime data if available
      const mergedDevices = allDevices.map(
        (device: {
          id: number;
          name?: string;
          ip_address?: string;
          mac_address?: string;
          is_ping_target: boolean;
        }) => {
          const uptimeInfo = uptimeMap.get(device.id);
          return {
            device_id: device.id,
            device_name: device.name || "",
            ip_address: device.ip_address,
            mac_address: device.mac_address,
            is_monitored: device.is_ping_target,
            uptime_percentage: uptimeInfo?.uptime_percentage || 0,
            total_pings: uptimeInfo?.total_pings || 0,
          };
        }
      );

      setDevices(mergedDevices);
    } catch (error) {
      console.error("Error loading devices:", error);
    } finally {
      setLoading(false);
    }
  }, [token]);

  React.useEffect(() => {
    loadDevices();
  }, [loadDevices]);

  const handleToggleMonitoring = async (deviceId: number, enable: boolean) => {
    setToggling(deviceId);

    // Optimistic update - update UI immediately
    setDevices((prevDevices) =>
      prevDevices.map((device) =>
        device.device_id === deviceId
          ? { ...device, is_monitored: enable }
          : device
      )
    );

    try {
      await onToggleMonitoring(deviceId, enable);
      // No need to reload - optimistic update already handled it
    } catch (error) {
      console.error("Error toggling monitoring:", error);
      // Revert optimistic update on error
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.device_id === deviceId
            ? { ...device, is_monitored: !enable }
            : device
        )
      );
    } finally {
      setToggling(null);
    }
  };

  const filteredDevices = devices
    .filter((device) => {
      const searchLower = searchTerm.toLowerCase();
      const deviceName = (device.device_name || "").toLowerCase();
      const ipAddress = (device.ip_address || "").toLowerCase();
      const macAddress = (device.mac_address || "").toLowerCase();

      return (
        deviceName.includes(searchLower) ||
        ipAddress.includes(searchLower) ||
        macAddress.includes(searchLower)
      );
    })
    .sort((a, b) => {
      const nameA = a.device_name || "";
      const nameB = b.device_name || "";

      // Check if names are text-based (contain letters) or numeric/unknown
      const isTextA = /[a-zA-Z]/.test(nameA);
      const isTextB = /[a-zA-Z]/.test(nameB);

      // If one is text and other isn't, text comes first
      if (isTextA && !isTextB) return -1;
      if (!isTextA && isTextB) return 1;

      // If both are same type, sort alphabetically
      return nameA.localeCompare(nameB);
    });

  const getUptimeColor = (uptime: number) => {
    if (uptime >= 95) return "text-green-600";
    if (uptime >= 80) return "text-yellow-600";
    return "text-red-600";
  };

  const t = React.useCallback(
    (key: string) => getT(`deviceMonitoring.management.${key}`),
    [getT]
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{t("title")}</CardTitle>
            <CardDescription>{t("description")}</CardDescription>
          </div>
          <Button
            onClick={() => setShowAddDialog(true)}
            size="sm"
            className="bg-green-600 hover:bg-green-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Device
          </Button>
        </div>
        <div className="relative max-w-sm">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={t("searchDevices")}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <RingLoader color="var(--color-logo-orange)" size={32} />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("deviceName")}</TableHead>
                <TableHead>{t("ipAddress")}</TableHead>
                <TableHead>{t("macAddress")}</TableHead>
                <TableHead>{t("uptime")} (Past 24 Hours)</TableHead>
                <TableHead>{t("monitoring")}</TableHead>
                <TableHead>{t("actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDevices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <Monitor className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">
                        {searchTerm ? t("noDevicesFound") : t("noDevices")}
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                filteredDevices.map((device) => (
                  <TableRow key={device.device_id}>
                    {/* Device Name Column */}
                    <TableCell className="font-medium">
                      {device.device_name || ""}
                    </TableCell>

                    {/* IP Address Column */}
                    <TableCell>
                      <span className="font-mono text-sm">
                        {device.ip_address || "—"}
                      </span>
                    </TableCell>

                    {/* MAC Address Column */}
                    <TableCell>
                      <span className="font-mono text-sm">
                        {device.mac_address || "—"}
                      </span>
                    </TableCell>

                    {/* Uptime Column - Only show for monitored devices */}
                    <TableCell>
                      {device.is_monitored ? (
                        <span
                          className={`font-medium ${getUptimeColor(
                            device.uptime_percentage
                          )}`}
                        >
                          {device.uptime_percentage.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
                    </TableCell>

                    {/* Monitoring Column - Status Only */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {device.is_monitored ? (
                          <>
                            <Wifi className="h-4 w-4 text-green-600" />
                            <span className="text-sm text-green-600 font-medium">
                              {t("monitoringOn")}
                            </span>
                          </>
                        ) : (
                          <>
                            <WifiOff className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground font-medium">
                              {t("monitoringOff")}
                            </span>
                          </>
                        )}
                      </div>
                    </TableCell>

                    {/* Actions Column - Only monitoring toggle */}
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleToggleMonitoring(
                            device.device_id,
                            !device.is_monitored
                          )
                        }
                        disabled={toggling === device.device_id}
                      >
                        {toggling === device.device_id ? (
                          <RingLoader color="currentColor" size={12} />
                        ) : device.is_monitored ? (
                          t("disable")
                        ) : (
                          t("enable")
                        )}
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>

      <AddDeviceDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onDeviceAdded={loadDevices}
        token={token || ""}
      />
    </Card>
  );
};

export default DeviceManagementTable;
