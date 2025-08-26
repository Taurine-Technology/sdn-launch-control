"use client";
import React, { useState } from "react";
import { NetworkDeviceDetails } from "@/lib/types";
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2Icon, PencilIcon } from "lucide-react";
import { useLanguage } from "@/context/languageContext";

interface EditDeviceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (
    deviceId: string,
    updatedData: Partial<NetworkDeviceDetails>
  ) => Promise<void>;
  device: NetworkDeviceDetails | null;
  isLoading?: boolean;
  error?: string;
}

interface FormData {
  name: string;
  mac_address: string;
  ip_address: string;
  device_type: string;
  operating_system: string;
  verified: boolean;
  number_of_ports?: number;
  [key: string]: unknown;
}

interface FormErrors {
  name?: string;
  mac_address?: string;
  ip_address?: string;
  device_type?: string;
  operating_system?: string;
  form?: string;
}

export const EditDeviceDialog: React.FC<EditDeviceDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  device,
  isLoading = false,
  error,
}) => {
  const { getT } = useLanguage();
  const [formData, setFormData] = useState<FormData>({
    name: "",
    mac_address: "",
    ip_address: "",
    device_type: "",
    operating_system: "",
    verified: false,
    number_of_ports: 0,
  });
  const [errors, setErrors] = useState<FormErrors>({});

  // Device type options with translations
  const DEVICE_TYPE_OPTIONS = [
    { value: "switch", label: getT("page.DevicesOverviewPage.switch") },
    {
      value: "access_point",
      label: getT("page.DevicesOverviewPage.access_point"),
    },
    { value: "server", label: getT("page.DevicesOverviewPage.server") },
    { value: "controller", label: getT("page.DevicesOverviewPage.controller") },
    { value: "vm", label: getT("page.DevicesOverviewPage.vm") },
    { value: "end_user", label: getT("page.DevicesOverviewPage.end_user") },
  ];

  // OS options with translations
  const OS_OPTIONS = [
    { value: "ubuntu_20_server", label: "Ubuntu 20 Server" },
    { value: "ubuntu_22_server", label: "Ubuntu 22 Server" },
    { value: "unknown", label: getT("common.unknown", "Unknown") },
    { value: "other", label: getT("common.other", "Other") },
  ];

  // Update form data when device changes
  React.useEffect(() => {
    if (device) {
      setFormData({
        name: device.name || "",
        mac_address: device.mac_address || "",
        ip_address: device.ip_address || "",
        device_type: device.device_type || "",
        operating_system: device.operating_system || "",
        verified: device.verified || false,
        number_of_ports: device.number_of_ports || 0,
      });
      setErrors({});
    }
  }, [device]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // MAC address validation (XX:XX:XX:XX:XX:XX format)
    if (
      !formData.mac_address ||
      !/^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$/.test(formData.mac_address)
    ) {
      newErrors.mac_address = getT(
        "components.network.edit_device_dialog.validation.mac_invalid"
      );
    }

    // Name validation
    if (!formData.name.trim()) {
      newErrors.name = getT(
        "components.network.edit_device_dialog.validation.name_required"
      );
    }

    // Device type validation
    if (!formData.device_type) {
      newErrors.device_type = getT(
        "components.network.edit_device_dialog.validation.device_type_required"
      );
    }

    // Operating system validation
    if (!formData.operating_system) {
      newErrors.operating_system = getT(
        "components.network.edit_device_dialog.validation.os_required"
      );
    }

    // IP address validation (optional but must be valid if provided)
    if (
      formData.ip_address &&
      !/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(
        formData.ip_address
      )
    ) {
      newErrors.ip_address = getT(
        "components.network.edit_device_dialog.validation.ip_invalid"
      );
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (
    field: keyof FormData,
    value: string | boolean | number
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const handleSave = async () => {
    if (!device || !validateForm()) {
      return;
    }

    try {
      await onSave(device.id, formData);
    } catch (err) {
      console.error("[EditDeviceDialog.tsx] handleSave", err);
      setErrors({
        form: getT(
          "components.network.edit_device_dialog.validation.update_failed"
        ),
      });
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
      setErrors({});
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PencilIcon className="h-5 w-5" />
            {getT("components.network.edit_device_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.network.edit_device_dialog.description")}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {errors.form && (
          <Alert variant="destructive">
            <AlertDescription>{errors.form}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-4 py-4">
          {/* MAC Address (read-only) */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="mac_address" className="text-right">
              {getT("components.network.edit_device_dialog.mac_address")}
            </Label>
            <Input
              id="mac_address"
              value={formData.mac_address}
              disabled
              className="col-span-3 bg-muted"
            />
          </div>

          {/* Device Name */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              {getT("components.network.edit_device_dialog.name")} *
            </Label>
            <div className="col-span-3">
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                className={errors.name ? "border-destructive" : ""}
              />
              {errors.name && (
                <p className="text-sm text-destructive mt-1">{errors.name}</p>
              )}
            </div>
          </div>

          {/* Device Type */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="device_type" className="text-right">
              {getT("components.network.edit_device_dialog.device_type")} *
            </Label>
            <div className="col-span-3">
              <Select
                value={formData.device_type}
                onValueChange={(value) =>
                  handleInputChange("device_type", value)
                }
              >
                <SelectTrigger
                  className={errors.device_type ? "border-destructive" : ""}
                >
                  <SelectValue
                    placeholder={getT(
                      "components.network.edit_device_dialog.device_type_placeholder"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {DEVICE_TYPE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.device_type && (
                <p className="text-sm text-destructive mt-1">
                  {errors.device_type}
                </p>
              )}
            </div>
          </div>

          {/* Operating System */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="operating_system" className="text-right">
              {getT("components.network.edit_device_dialog.operating_system")} *
            </Label>
            <div className="col-span-3">
              <Select
                value={formData.operating_system}
                onValueChange={(value) =>
                  handleInputChange("operating_system", value)
                }
              >
                <SelectTrigger
                  className={
                    errors.operating_system ? "border-destructive" : ""
                  }
                >
                  <SelectValue
                    placeholder={getT(
                      "components.network.edit_device_dialog.os_placeholder"
                    )}
                  />
                </SelectTrigger>
                <SelectContent>
                  {OS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.operating_system && (
                <p className="text-sm text-destructive mt-1">
                  {errors.operating_system}
                </p>
              )}
            </div>
          </div>

          {/* IP Address */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="ip_address" className="text-right">
              {getT("components.network.edit_device_dialog.ip_address")}
            </Label>
            <div className="col-span-3">
              <Input
                id="ip_address"
                value={formData.ip_address}
                onChange={(e) =>
                  handleInputChange("ip_address", e.target.value)
                }
                placeholder={getT(
                  "components.network.edit_device_dialog.ip_address_placeholder"
                )}
                className={errors.ip_address ? "border-destructive" : ""}
              />
              {errors.ip_address && (
                <p className="text-sm text-destructive mt-1">
                  {errors.ip_address}
                </p>
              )}
            </div>
          </div>

          {/* Verification Status */}
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="verified" className="text-right">
              {getT("components.network.edit_device_dialog.verified")}
            </Label>
            <div className="col-span-3">
              <Select
                value={formData.verified.toString()}
                onValueChange={(value) =>
                  handleInputChange("verified", value === "true")
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">
                    {getT(
                      "components.network.edit_device_dialog.verified_true"
                    )}
                  </SelectItem>
                  <SelectItem value="false">
                    {getT(
                      "components.network.edit_device_dialog.verified_false"
                    )}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            {getT("components.network.edit_device_dialog.cancel")}
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                {getT("components.network.edit_device_dialog.saving")}
              </>
            ) : (
              getT("components.network.edit_device_dialog.save")
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
