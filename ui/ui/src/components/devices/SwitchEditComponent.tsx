import { useState, useEffect } from "react";
import { NetworkDeviceDetails } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Loader2Icon } from "lucide-react";
import { toast } from "sonner";
import { updateSwitch } from "@/lib/devices";
import { useLanguage } from "@/context/languageContext";

const OS_OPTIONS = [
  { value: "ubuntu_20_server", label: "Ubuntu 20 Server" },
  { value: "ubuntu_22_server", label: "Ubuntu 22 Server" },
  { value: "unknown", label: "Unknown" },
  { value: "other", label: "Other" },
];

interface SwitchEditComponentProps {
  switchData: NetworkDeviceDetails;
  onUpdate: () => void;
}

export default function SwitchEditComponent({
  switchData,
  onUpdate,
}: SwitchEditComponentProps) {
  const { getT } = useLanguage();
  const [formData, setFormData] = useState<{
    id: string;
    device_type: string;
    lan_ip_address: string;
    name: string;
    num_ports: string;
    os_type: string;
    ovs_version: string;
    openflow_version: string;
  }>({
    id: String(switchData.id || ""),
    device_type: "switch",
    lan_ip_address: String(switchData.lan_ip_address || ""),
    name: String(switchData.name || ""),
    num_ports: String(switchData.num_ports || ""),
    os_type: String(switchData.os_type || ""),
    ovs_version: String(switchData.ovs_version || ""),
    openflow_version: String(switchData.openflow_version || ""),
  });
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaveEnabled, setIsSaveEnabled] = useState(false);

  useEffect(() => {
    if (isEditing) {
      setIsSaveEnabled(hasChanges());
    } else {
      setIsSaveEnabled(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData, isEditing]);

  function hasChanges() {
    return (
      formData.lan_ip_address !== switchData.lan_ip_address ||
      formData.name !== switchData.name ||
      formData.num_ports !== switchData.num_ports ||
      formData.os_type !== switchData.os_type ||
      formData.ovs_version !== switchData.ovs_version ||
      formData.openflow_version !== switchData.openflow_version
    );
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  }

  function handleOsChange(value: string) {
    setFormData((prev) => ({ ...prev, os_type: value }));
  }

  function toggleEditMode() {
    setIsEditing((editing) => !editing);
    if (isEditing) {
      setFormData({
        id: switchData.id,
        device_type: "switch",
        lan_ip_address: String(switchData.lan_ip_address || ""),
        name: switchData.name || "",
        num_ports: String(switchData.num_ports || ""),
        os_type: String(switchData.os_type || ""),
        ovs_version: String(switchData.ovs_version || ""),
        openflow_version: String(switchData.openflow_version || ""),
      });
    }
  }

  async function handleSave() {
    if (!hasChanges()) {
      setIsEditing(false);
      return;
    }
    setIsLoading(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken") || ""
          : "";

      const updatedData = await updateSwitch(token, formData.id, formData);
      console.log("[SWITCHEDITCOMPONENT.tsx] updatedData", updatedData);
      setIsEditing(false);
      toast.success(getT("components.devices.switch_edit.success"));
      onUpdate();
    } catch {
      toast.error(getT("components.devices.switch_edit.error"));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="w-full flex justify-center pt-6">
      <Card className="w-full min-h-[320px] min-w-[320px] ">
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">
              {getT("components.devices.switch_edit.title")}
            </h2>
            {/* You can add a connection indicator here if needed */}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="name">
                {getT("components.devices.switch_edit.name")}
              </Label>
              <Input
                id="name"
                name="name"
                value={formData.name || ""}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
            </div>
            <div>
              <Label htmlFor="lan_ip_address">
                {getT("components.devices.switch_edit.ip_address")}
              </Label>
              <Input
                id="lan_ip_address"
                name="lan_ip_address"
                value={formData.lan_ip_address}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
            </div>
            <div>
              <Label htmlFor="num_ports">
                {getT("components.devices.switch_edit.number_of_ports")}
              </Label>
              <Input
                id="num_ports"
                name="num_ports"
                value={formData.num_ports || ""}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
            </div>
            <div>
              <Label htmlFor="os_type">
                {getT("components.devices.switch_edit.operating_system")}
              </Label>
              <Select
                value={formData.os_type || ""}
                onValueChange={handleOsChange}
                disabled={!isEditing}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select OS" />
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
            {!!(
              (switchData.ovs_version &&
                String(switchData.ovs_version).trim()) ||
              (switchData.openflow_version &&
                String(switchData.openflow_version).trim())
            ) && (
              <>
                {switchData.ovs_version &&
                  String(switchData.ovs_version).trim() && (
                    <div>
                      <Label htmlFor="ovs_version">
                        {getT("components.devices.switch_edit.ovs_version")}
                      </Label>
                      <Input
                        id="ovs_version"
                        name="ovs_version"
                        value={formData.ovs_version || ""}
                        onChange={handleInputChange}
                        disabled={!isEditing}
                      />
                    </div>
                  )}
                {switchData.openflow_version &&
                  String(switchData.openflow_version).trim() && (
                    <div>
                      <Label htmlFor="openflow_version">
                        {getT(
                          "components.devices.switch_edit.openflow_version"
                        )}
                      </Label>
                      <Input
                        id="openflow_version"
                        name="openflow_version"
                        value={formData.openflow_version || ""}
                        onChange={handleInputChange}
                        disabled={!isEditing}
                      />
                    </div>
                  )}
              </>
            )}
          </div>
          <div className="flex justify-end gap-2 mt-6">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={toggleEditMode}
                  type="button"
                >
                  {getT("components.devices.switch_edit.cancel")}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={!isSaveEnabled || isLoading}
                >
                  {isLoading ? (
                    <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                  ) : null}
                  {isLoading
                    ? getT("components.devices.switch_edit.saving")
                    : getT("components.devices.switch_edit.save")}
                </Button>
              </>
            ) : (
              <Button onClick={toggleEditMode}>
                {getT("components.devices.switch_edit.edit")}
              </Button>
            )}
          </div>
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
              <Loader2Icon className="animate-spin w-8 h-8" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
