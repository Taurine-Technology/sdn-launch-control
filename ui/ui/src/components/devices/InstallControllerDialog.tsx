"use client";

import { useState, useEffect, useCallback } from "react";

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
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2Icon, AlertTriangleIcon } from "lucide-react";
import { toast } from "sonner";
import { installController } from "@/lib/software";
import { RingLoader } from "react-spinners";
import { useLanguage } from "@/context/languageContext";

interface InstallControllerFormData {
  name: string;
  lan_ip_address: string;
  username: string;
  password: string;
  os_type: string;
  controller_type: string;
  device_type: string;
}

interface InstallControllerDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export default function InstallControllerDialog({
  isOpen,
  onClose,
  onSuccess,
}: InstallControllerDialogProps) {
  const { getT } = useLanguage();

  // OS options with translations
  const OS_OPTIONS = [
    { value: "ubuntu_22_server", label: "Ubuntu 22.04 Server" },
    { value: "ubuntu_20_server", label: "Ubuntu 20.04 Server" },
  ];

  // Controller type options with translations
  const CONTROLLER_TYPE_OPTIONS = [
    { value: "odl", label: "Opendaylight" },
    // { value: "onos", label: "ONOS" }, // Disabled
  ];

  const [formData, setFormData] = useState<InstallControllerFormData>({
    name: "",
    lan_ip_address: "",
    username: "",
    password: "",
    os_type: "ubuntu_22_server",
    controller_type: "odl",
    device_type: "controller",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFormValid, setIsFormValid] = useState(false);
  const [ipError, setIpError] = useState<string | null>(null);

  const validateForm = useCallback(() => {
    // IPv4 validation regex
    const IPV4_REGEX =
      /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

    const validateIpAddress = (ip: string): boolean => {
      if (!ip.trim()) return false;
      return IPV4_REGEX.test(ip.trim());
    };

    const isIpValid = validateIpAddress(formData.lan_ip_address);
    setIpError(
      isIpValid || !formData.lan_ip_address
        ? null
        : getT(
            "components.devices.install_controller_dialog.validation.ip_invalid"
          )
    );

    return (
      formData.name.trim() !== "" &&
      formData.lan_ip_address.trim() !== "" &&
      isIpValid &&
      formData.username.trim() !== "" &&
      formData.password.trim() !== "" &&
      formData.os_type !== "" &&
      formData.controller_type !== ""
    );
  }, [formData, getT]);

  useEffect(() => {
    setIsFormValid(validateForm());
  }, [formData, validateForm]);

  useEffect(() => {
    if (isOpen && !isLoading) {
      // Reset form when dialog opens
      setFormData({
        name: "",
        lan_ip_address: "",
        username: "",
        password: "",
        os_type: "ubuntu_22_server",
        controller_type: "odl",
        device_type: "controller",
      });
      setError(null);
    }
  }, [isOpen, isLoading]);

  const handleInputChange = (
    field: keyof InstallControllerFormData,
    value: string
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error(
          getT(
            "components.devices.install_controller_dialog.validation.no_token"
          )
        );
      }

      // Extract controller_type for URL and remove from body data
      const { controller_type, ...bodyData } = formData;

      const response = await installController(
        token,
        controller_type,
        bodyData
      );

      if (response.status === "success") {
        onSuccess(response.message);
      } else {
        throw new Error(
          response.message ||
            getT(
              "components.devices.install_controller_dialog.validation.installation_failed"
            )
        );
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : getT(
              "components.devices.install_controller_dialog.validation.failed_to_install"
            );
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {getT("components.devices.install_controller_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.devices.install_controller_dialog.description")}
          </DialogDescription>
        </DialogHeader>

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10 rounded-lg">
            <div className="flex flex-col items-center gap-2">
              <RingLoader color="#7456FD" size={60} loading={true} />
              <p className="text-sm text-muted-foreground">
                {getT(
                  "components.devices.install_controller_dialog.installing_message"
                )}
              </p>
            </div>
          </div>
        )}

        <div className="grid gap-4 py-4">
          {error && (
            <Alert variant="destructive">
              <AlertTriangleIcon className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid gap-2">
            <Label htmlFor="name">Device Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange("name", e.target.value)}
              placeholder="Enter device name"
              disabled={isLoading}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="lan_ip_address">LAN IP Address</Label>
            <Input
              id="lan_ip_address"
              value={formData.lan_ip_address}
              onChange={(e) =>
                handleInputChange("lan_ip_address", e.target.value)
              }
              placeholder="192.168.1.100"
              disabled={isLoading}
              className={ipError ? "border-red-500" : ""}
            />
            {ipError && <p className="text-sm text-red-500 mt-1">{ipError}</p>}
          </div>

          <div className="grid gap-2">
            <Label htmlFor="username">Username</Label>
            <Input
              id="username"
              value={formData.username}
              onChange={(e) => handleInputChange("username", e.target.value)}
              placeholder="Enter username"
              disabled={isLoading}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange("password", e.target.value)}
              placeholder="Enter password"
              disabled={isLoading}
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="os_type">Operating System</Label>
            <Select
              value={formData.os_type}
              onValueChange={(value) => handleInputChange("os_type", value)}
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select operating system" />
              </SelectTrigger>
              <SelectContent>
                {OS_OPTIONS.map((os) => (
                  <SelectItem key={os.value} value={os.value}>
                    {os.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="controller_type">Controller Type</Label>
            <Select
              value={formData.controller_type}
              onValueChange={(value) =>
                handleInputChange("controller_type", value)
              }
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select controller type" />
              </SelectTrigger>
              <SelectContent>
                {CONTROLLER_TYPE_OPTIONS.map((controller) => (
                  <SelectItem key={controller.value} value={controller.value}>
                    {controller.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {formData.controller_type === "onos" && (
            <Alert>
              <AlertTriangleIcon className="h-4 w-4" />
              <AlertDescription>
                ONOS is no longer maintained and may result in instability if
                used in a network.
              </AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading || !isFormValid}>
            {isLoading ? (
              <>
                <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                Installing...
              </>
            ) : (
              "Install Controller"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
