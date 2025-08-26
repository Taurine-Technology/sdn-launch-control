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

interface InstallOvsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onInstall: (payload: Record<string, unknown>) => Promise<void>;
  switches: NetworkDeviceDetails[];
  isLoading: boolean;
  response?: string;
  responseType?: "success" | "error";
  disableClose?: boolean;
}
import { useState, useEffect } from "react";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

import { useLanguage } from "@/context/languageContext";
import { NetworkDeviceDetails } from "@/lib/types";

const OS_OPTIONS = [
  { value: "ubuntu_22_server", label: "Ubuntu 22.04 Server" },
  { value: "ubuntu_20_server", label: "Ubuntu 20.04 Server" },
];
const DEVICE_TYPE_OPTIONS = [
  { value: "switch", label: "Switch" },
  { value: "access_point", label: "Access Point" },
  { value: "server", label: "Server" },
  { value: "controller", label: "Controller" },
];

// Simple IPv4 regex
function isValidIp(ip: string): boolean {
  return /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(
    ip
  );
}

function isValidUrl(url: string): boolean {
  // Check for empty or whitespace-only strings
  if (!url || url.trim().length === 0) {
    return false;
  }

  // Check for spaces (URLs cannot contain unencoded spaces)
  if (url.includes(" ")) {
    return false;
  }

  try {
    const urlObject = new URL(url);

    // Check for valid protocols
    const validProtocols = ["http:", "https:", "ftp:", "ftps:"];
    if (!validProtocols.includes(urlObject.protocol)) {
      return false;
    }

    // Check for valid hostname/host (domain or IP)
    if (!urlObject.hostname || urlObject.hostname.length === 0) {
      return false;
    }

    // Additional validation for proper domain structure
    // Ensure hostname doesn't start or end with dots
    if (
      urlObject.hostname.startsWith(".") ||
      urlObject.hostname.endsWith(".")
    ) {
      return false;
    }

    // Check for consecutive dots in hostname
    if (urlObject.hostname.includes("..")) {
      return false;
    }

    return true;
  } catch {
    // URL constructor throws TypeError for invalid URLs
    return false;
  }
}

export const InstallOvsDialog: React.FC<InstallOvsDialogProps> = ({
  isOpen,
  onClose,
  onInstall,
  isLoading,
  disableClose,
}) => {
  const { getT } = useLanguage();
  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [deviceType, setDeviceType] = useState("switch");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [operatingSystem, setOperatingSystem] = useState("ubuntu_22_server");
  const [apiUrl, setApiUrl] = useState("");
  const [isPi, setIsPi] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);
  const [ipError, setIpError] = useState<string | null>(null);
  const [urlError, setUrlError] = useState<string | null>(null);

  useEffect(() => {
    setIpError(host ? (isValidIp(host) ? null : "Invalid IP address") : null);
    setUrlError(apiUrl ? (isValidUrl(apiUrl) ? null : "Invalid URL") : null);
    setIsFormValid(
      !!name &&
        !!host &&
        !!username &&
        !!password &&
        !!apiUrl &&
        isValidIp(host) &&
        isValidUrl(apiUrl)
    );
  }, [name, host, username, password, apiUrl]);

  useEffect(() => {
    if (!isOpen) {
      setName("");
      setHost("");
      setDeviceType("switch");
      setUsername("");
      setPassword("");
      setOperatingSystem("ubuntu_22_server");
      setApiUrl("");
      setIsPi(false);
    }
  }, [isOpen]);

  const handleInstall = async () => {
    await onInstall({
      name,
      device_type: deviceType,
      os_type: operatingSystem,
      lan_ip_address: host,
      username,
      password,
      api_url: apiUrl,
      is_pi: isPi,
    });
  };

  return (
    <Dialog
      open={isOpen}
      onOpenChange={() => {
        if (!disableClose) onClose();
      }}
      modal={true}
      // Prevent closing by escape or backdrop if disableClose is true
      // shadcn/ui Dialog does not have direct props for this, so we handle in onOpenChange
    >
      <DialogContent
        onInteractOutside={disableClose ? (e) => e.preventDefault() : undefined}
        onEscapeKeyDown={disableClose ? (e) => e.preventDefault() : undefined}
        onPointerDownOutside={
          disableClose ? (e) => e.preventDefault() : undefined
        }
      >
        {isLoading && (
          <div className="absolute inset-0 z-50 flex items-center justify-center bg-background/80">
            <RingLoader color="#7456FD" size={60} />
          </div>
        )}
        <DialogHeader>
          <DialogTitle>
            {getT("page.SwitchesPage.install_ovs_dialog_title") ||
              "Install Open vSwitch"}
          </DialogTitle>
          <DialogDescription>
            {getT("page.SwitchesPage.install_ovs_dialog_description") ||
              "Fill in your device's details to install OVS and the Taurine Tech software stack."}
          </DialogDescription>
        </DialogHeader>
        <div
          className={`flex flex-col gap-4 mt-2 ${
            isLoading ? "pointer-events-none opacity-60" : ""
          }`}
        >
          <Label htmlFor="name">
            {getT("page.SwitchesPage.switch_name") || "Device Name"}
          </Label>
          <Input
            id="name"
            placeholder={
              getT("page.SwitchesPage.switch_name_placeholder") || "Switch name"
            }
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isLoading}
            required
          />

          <Label htmlFor="host">
            {getT("page.SwitchesPage.switch_ip_address") || "IP Address"}
          </Label>
          <Input
            id="host"
            placeholder={
              getT("page.SwitchesPage.switch_ip_address_placeholder") ||
              "192.168.1.10"
            }
            value={host}
            onChange={(e) => setHost(e.target.value)}
            disabled={isLoading}
            required
          />
          {ipError && (
            <span className="text-red-500 text-xs">
              {getT("page.SwitchesPage.invalid_ip_address") || ipError}
            </span>
          )}

          <Label htmlFor="username">
            {getT("page.SwitchesPage.switch_username") || "Username"}
          </Label>
          <Input
            id="username"
            placeholder={
              getT("page.SwitchesPage.switch_username_placeholder") || "admin"
            }
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={isLoading}
            required
          />

          <Label htmlFor="password">
            {getT("page.SwitchesPage.switch_password") || "Password"}
          </Label>
          <Input
            id="password"
            placeholder={
              getT("page.SwitchesPage.switch_password_placeholder") || "Password"
            }
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isLoading}
            required
          />

          <Label htmlFor="api-url">
            {getT("page.SwitchesPage.switch_api_url") || "API URL"}
          </Label>
          <Input
            id="api-url"
            placeholder={
              getT("page.SwitchesPage.switch_api_url_placeholder") ||
              "http://192.168.1.10:8080/api"
            }
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            disabled={isLoading}
            required
          />
          {urlError && (
            <span className="text-red-500 text-xs">
              {getT("page.SwitchesPage.invalid_api_url") || urlError}
            </span>
          )}

          <Label htmlFor="os-select">
            {getT("page.SwitchesPage.switch_operating_system") || "Operating System"}
          </Label>
          <Select
            value={operatingSystem}
            onValueChange={setOperatingSystem}
            disabled={isLoading}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  getT("page.SwitchesPage.switch_operating_system_placeholder") ||
                  "Select OS"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {OS_OPTIONS.map((os) => (
                <SelectItem key={os.value} value={os.value}>
                  {getT("page.SwitchesPage.os_" + os.value) || os.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Label htmlFor="device-type-select">
            {getT("page.SwitchesPage.switch_device_type") || "Device Type"}
          </Label>
          <Select
            value={deviceType}
            onValueChange={setDeviceType}
            disabled={true}
          >
            <SelectTrigger>
              <SelectValue
                placeholder={
                  getT("page.SwitchesPage.switch_device_type_placeholder") ||
                  "Select device type"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {DEVICE_TYPE_OPTIONS.map((dt) => (
                <SelectItem key={dt.value} value={dt.value}>
                  {getT("page.SwitchesPage.device_type_" + dt.value) || dt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex flex-row items-center gap-2 mt-2">
            <Checkbox
              id="is-pi-switch"
              checked={isPi}
              onCheckedChange={(checked) => setIsPi(!!checked)}
              disabled={isLoading}
            />
            <Label htmlFor="is-pi-switch">
              {getT("page.SwitchesPage.is_raspberry_pi") || "Is Raspberry Pi?"}
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            {getT("page.SwitchesPage.cancel") || "Cancel"}
          </Button>
          <Button onClick={handleInstall} disabled={!isFormValid || isLoading}>
            {isLoading
              ? getT("page.SwitchesPage.installing") || "Installing..."
              : getT("page.SwitchesPage.install") || "Install OVS"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default InstallOvsDialog;
