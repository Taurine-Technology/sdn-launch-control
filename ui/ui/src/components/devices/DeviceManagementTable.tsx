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
import { 
  Monitor, 
  Pencil,
  Search,
  Trash2,
  Wifi,
  WifiOff
} from "lucide-react";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";
import { 
  fetchDeviceUptimeStatus,
  updateDeviceName,
  deleteDevice
} from "@/lib/deviceMonitoring";
import { createAxiosInstanceWithToken } from "@/lib/axiosInstance";
import { DeviceUptimeStatus } from "@/lib/types";
import RingLoader from "react-spinners/RingLoader";

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
  const [deleting, setDeleting] = React.useState<number | null>(null);

  const loadDevices = React.useCallback(async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      // Fetch uptime status for devices that have been pinged
      const uptimeData = await fetchDeviceUptimeStatus(token, "24 hours");
      
      // Create a map of device_id -> uptime data
      const uptimeMap = new Map(
        uptimeData.map(d => [d.device_id, d])
      );
      
      // Fetch all network devices (paginated, so get first page with large size)
      const axiosInstance = createAxiosInstanceWithToken(token);
      const { data: allDevicesResponse } = await axiosInstance.get("/network-devices/?page_size=200");
      const allDevices = allDevicesResponse.results || allDevicesResponse;
      
      // Merge: for each device, add uptime data if available
      const mergedDevices = allDevices.map((device: { 
        id: number; 
        name?: string; 
        ip_address?: string; 
        mac_address?: string; 
        is_ping_target: boolean;
      }) => {
        const uptimeInfo = uptimeMap.get(device.id);
        return {
          device_id: device.id,
          device_name: device.name || device.ip_address || 'Unknown Device',
          ip_address: device.ip_address,
          mac_address: device.mac_address,
          is_monitored: device.is_ping_target,
          uptime_percentage: uptimeInfo?.uptime_percentage || 0,
          total_pings: uptimeInfo?.total_pings || 0,
        };
      });
      
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

  // Log device data for debugging
  React.useEffect(() => {
    if (devices.length > 0) {
      console.log('[DEVICE MANAGEMENT] Loaded devices:', devices);
      console.log('[DEVICE MANAGEMENT] Sample device:', devices[0]);
      console.log('[DEVICE MANAGEMENT] Device fields:', {
        device_id: devices[0].device_id,
        device_name: devices[0].device_name,
        uptime_percentage: devices[0].uptime_percentage,
        total_pings: devices[0].total_pings,
        is_monitored: devices[0].is_monitored,
      });
    }
  }, [devices]);

  const handleToggleMonitoring = async (deviceId: number, enable: boolean) => {
    setToggling(deviceId);
    
    // Optimistic update - update UI immediately
    setDevices(prevDevices => 
      prevDevices.map(device => 
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
      setDevices(prevDevices => 
        prevDevices.map(device => 
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
    .filter(device =>
      (device.device_name || '').toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      const nameA = a.device_name || '';
      const nameB = b.device_name || '';
      
      // Check if names are text-based (contain letters) or numeric/unknown
      const isTextA = /[a-zA-Z]/.test(nameA);
      const isTextB = /[a-zA-Z]/.test(nameB);
      
      // If one is text and other isn't, text comes first
      if (isTextA && !isTextB) return -1;
      if (!isTextA && isTextB) return 1;
      
      // If both are same type, sort alphabetically
      return nameA.localeCompare(nameB);
    });

  const [editingDevice, setEditingDevice] = React.useState<number | null>(null);
  const [editedName, setEditedName] = React.useState<string>("");
  const [savingName, setSavingName] = React.useState(false);

  const getUptimeColor = (uptime: number) => {
    if (uptime >= 95) return "text-green-600";
    if (uptime >= 80) return "text-yellow-600";
    return "text-red-600";
  };

  const handleSaveDeviceName = async (device: DeviceUptimeStatus) => {
    if (!editedName.trim() || editedName === device.device_name) {
      setEditingDevice(null);
      return;
    }

    setSavingName(true);
    const newName = editedName.trim();
    const originalName = device.device_name;
    
    // Optimistic update - update UI immediately
    setDevices(prevDevices => 
      prevDevices.map(d => 
        d.device_id === device.device_id 
          ? { ...d, device_name: newName }
          : d
      )
    );
    
    try {
      await updateDeviceName(token || '', device.ip_address, device.mac_address, newName);
      setEditingDevice(null);
      // No need to reload - optimistic update already handled it
    } catch (error) {
      console.error("Error updating device name:", error);
      // Revert optimistic update on error
      setDevices(prevDevices => 
        prevDevices.map(d => 
          d.device_id === device.device_id 
            ? { ...d, device_name: originalName }
            : d
        )
      );
      alert("Failed to update device name. Please try again.");
    } finally {
      setSavingName(false);
    }
  };

  const handleDeleteDevice = async (device: DeviceUptimeStatus) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${device.device_name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmed) return;

    setDeleting(device.device_id);
    
    // Optimistic update - remove device from UI immediately
    setDevices(prevDevices => 
      prevDevices.filter(d => d.device_id !== device.device_id)
    );

    try {
      await deleteDevice(token || '', device.ip_address, device.mac_address);
      // No need to reload - optimistic update already handled it
    } catch (error) {
      console.error("Error deleting device:", error);
      // Revert optimistic update on error - add device back
      setDevices(prevDevices => [...prevDevices, device]);
      alert("Failed to delete device. Please try again.");
    } finally {
      setDeleting(null);
    }
  };

  const t = React.useCallback((key: string) => getT(`deviceMonitoring.management.${key}`), [getT]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
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
                <TableHead>{t("uptime")} (Past 24 Hours)</TableHead>
                <TableHead>{t("monitoring")}</TableHead>
                <TableHead>{t("actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDevices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8">
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
                    {/* Device Name Column with Inline Editing */}
                    <TableCell className="font-medium">
                      {editingDevice === device.device_id ? (
                        <div className="flex items-center gap-2">
                          <Input
                            value={editedName}
                            onChange={(e) => setEditedName(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                handleSaveDeviceName(device);
                              } else if (e.key === "Escape") {
                                setEditingDevice(null);
                              }
                            }}
                            disabled={savingName}
                            className="h-8"
                            autoFocus
                          />
                          <Button
                            size="sm"
                            onClick={() => handleSaveDeviceName(device)}
                            disabled={savingName}
                          >
                            {savingName ? <RingLoader color="currentColor" size={12} /> : "Save"}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setEditingDevice(null)}
                            disabled={savingName}
                          >
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2">
                          {device.device_name}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setEditingDevice(device.device_id);
                              setEditedName(device.device_name);
                            }}
                            className="h-6 w-6 p-0"
                          >
                            <Pencil className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                    </TableCell>
                    
                    {/* Uptime Column - Just Percentage */}
                    <TableCell>
                      <span className={`font-medium ${getUptimeColor(device.uptime_percentage)}`}>
                        {device.uptime_percentage.toFixed(1)}%
                      </span>
                    </TableCell>
                    
                    {/* Monitoring Column - Status Only */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {device.is_monitored ? (
                          <>
                            <Wifi className="h-4 w-4 text-green-600" />
                            <span className="text-sm text-green-600 font-medium">{t("monitoringOn")}</span>
                          </>
                        ) : (
                          <>
                            <WifiOff className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm text-muted-foreground font-medium">{t("monitoringOff")}</span>
                          </>
                        )}
                      </div>
                    </TableCell>
                    
                    {/* Actions Column */}
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleToggleMonitoring(device.device_id, !device.is_monitored)}
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
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => handleDeleteDevice(device)}
                          disabled={deleting === device.device_id}
                          title="Delete device"
                        >
                          {deleting === device.device_id ? (
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
};

export default DeviceManagementTable;
