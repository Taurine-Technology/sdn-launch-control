"use client";

import * as React from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { createNetworkDevice } from "@/lib/deviceMonitoring";
import { DEVICE_TYPES, OS_TYPES } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";
import RingLoader from "react-spinners/RingLoader";

interface AddDeviceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDeviceAdded: () => void;
  token: string;
}

const AddDeviceDialog: React.FC<AddDeviceDialogProps> = ({
  open,
  onOpenChange,
  onDeviceAdded,
  token,
}) => {
  const { getT } = useLanguage();
  const [formData, setFormData] = React.useState({
    name: "",
    device_type: "",
    operating_system: "",
    ip_address: "",
    mac_address: "",
    is_ping_target: true,
  });
  const [loading, setLoading] = React.useState(false);
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  // Validation functions
  const validateIPAddress = (ip: string): boolean => {
    const ipv4Regex =
      /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    const ipv6Regex = /^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    return ipv4Regex.test(ip) || ipv6Regex.test(ip);
  };

  const validateMACAddress = (mac: string): boolean => {
    if (!mac) return true; // MAC is optional
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/;
    return macRegex.test(mac);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Device name is required";
    }

    if (!formData.device_type) {
      newErrors.device_type = "Device type is required";
    }

    if (!formData.operating_system) {
      newErrors.operating_system = "Operating system is required";
    }

    if (!formData.ip_address.trim()) {
      newErrors.ip_address = "IP address is required";
    } else if (!validateIPAddress(formData.ip_address)) {
      newErrors.ip_address = "Please enter a valid IP address (IPv4 or IPv6)";
    }

    if (formData.mac_address && !validateMACAddress(formData.mac_address)) {
      newErrors.mac_address =
        "Please enter a valid MAC address (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      const deviceData = {
        name: formData.name.trim(),
        device_type: formData.device_type,
        operating_system: formData.operating_system,
        ip_address: formData.ip_address.trim(),
        mac_address: formData.mac_address.trim() || undefined,
        is_ping_target: formData.is_ping_target,
      };

      await createNetworkDevice(token, deviceData);

      toast.success("Device added successfully");
      onDeviceAdded();
      onOpenChange(false);

      // Reset form
      setFormData({
        name: "",
        device_type: "",
        operating_system: "",
        ip_address: "",
        mac_address: "",
        is_ping_target: true,
      });
      setErrors({});
    } catch (error: any) {
      console.error("Error creating device:", error);

      if (error.response?.status === 400 || error.response?.status === 409) {
        toast.error(
          error.response?.data?.message ||
            "Device already exists or invalid data"
        );
      } else {
        toast.error("Failed to add device. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add New Device</DialogTitle>
          <DialogDescription>
            Add a new network device to monitor. All fields except MAC address
            are required.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Device Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange("name", e.target.value)}
              placeholder="Enter device name"
              className={errors.name ? "border-red-500" : ""}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="device_type">Device Type *</Label>
            <Select
              value={formData.device_type}
              onValueChange={(value) => handleInputChange("device_type", value)}
            >
              <SelectTrigger
                className={errors.device_type ? "border-red-500" : ""}
              >
                <SelectValue placeholder="Select device type" />
              </SelectTrigger>
              <SelectContent>
                {DEVICE_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.device_type && (
              <p className="text-sm text-red-500">{errors.device_type}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="operating_system">Operating System *</Label>
            <Select
              value={formData.operating_system}
              onValueChange={(value) =>
                handleInputChange("operating_system", value)
              }
            >
              <SelectTrigger
                className={errors.operating_system ? "border-red-500" : ""}
              >
                <SelectValue placeholder="Select operating system" />
              </SelectTrigger>
              <SelectContent>
                {OS_TYPES.map((os) => (
                  <SelectItem key={os.value} value={os.value}>
                    {os.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.operating_system && (
              <p className="text-sm text-red-500">{errors.operating_system}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="ip_address">IP Address *</Label>
            <Input
              id="ip_address"
              value={formData.ip_address}
              onChange={(e) => handleInputChange("ip_address", e.target.value)}
              placeholder="192.168.1.100 or 2001:db8::1"
              className={errors.ip_address ? "border-red-500" : ""}
            />
            {errors.ip_address && (
              <p className="text-sm text-red-500">{errors.ip_address}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="mac_address">MAC Address</Label>
            <Input
              id="mac_address"
              value={formData.mac_address}
              onChange={(e) => handleInputChange("mac_address", e.target.value)}
              placeholder="AA:BB:CC:DD:EE:FF"
              className={errors.mac_address ? "border-red-500" : ""}
            />
            {errors.mac_address && (
              <p className="text-sm text-red-500">{errors.mac_address}</p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="is_ping_target"
              checked={formData.is_ping_target}
              onCheckedChange={(checked) =>
                handleInputChange("is_ping_target", checked as boolean)
              }
            />
            <Label htmlFor="is_ping_target">Enable monitoring</Label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <RingLoader color="currentColor" size={16} className="mr-2" />
                  Adding...
                </>
              ) : (
                "Add Device"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default AddDeviceDialog;
