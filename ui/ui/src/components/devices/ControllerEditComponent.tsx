import { useState, useEffect } from "react";
import { Controller } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2Icon } from "lucide-react";
import { toast } from "sonner";
import { updateController } from "@/lib/devices";
import { useLanguage } from "@/context/languageContext";

interface ControllerEditComponentProps {
  controllerData: Controller;
  onUpdate: () => void;
}

export default function ControllerEditComponent({
  controllerData,
  onUpdate,
}: ControllerEditComponentProps) {
  const { getT } = useLanguage();
  const [formData, setFormData] = useState<{
    id: number;
    lan_ip_address: string;
    port_num: string;
  }>({
    id: controllerData?.id || 0,
    lan_ip_address: controllerData?.lan_ip_address || "",
    port_num: String(controllerData?.port_num || ""),
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

  // Update form data when controllerData changes
  useEffect(() => {
    if (controllerData) {
      setFormData({
        id: controllerData.id,
        lan_ip_address: controllerData.lan_ip_address || "",
        port_num: String(controllerData.port_num || ""),
      });
    }
  }, [controllerData]);

  function hasChanges() {
    if (!controllerData) return false;
    return (
      formData.lan_ip_address !== controllerData.lan_ip_address ||
      formData.port_num !== String(controllerData.port_num)
    );
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  }

  function toggleEditMode() {
    setIsEditing((editing) => !editing);
    if (isEditing && controllerData) {
      setFormData({
        id: controllerData.id,
        lan_ip_address: controllerData.lan_ip_address || "",
        port_num: String(controllerData.port_num || ""),
      });
    }
  }

  async function handleSave() {
    if (!hasChanges() || !controllerData) {
      setIsEditing(false);
      return;
    }
    setIsLoading(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken") || ""
          : "";

      const updatedData = await updateController(token, String(formData.id), {
        lan_ip_address: formData.lan_ip_address,
        port_num: parseInt(formData.port_num),
      });
      console.log("[CONTROLLEREDITCOMPONENT.tsx] updatedData", updatedData);
      setIsEditing(false);
      toast.success(getT("components.devices.controller_edit.update_success"));
      onUpdate();
    } catch {
      toast.error(getT("components.devices.controller_edit.update_error"));
    } finally {
      setIsLoading(false);
    }
  }

  // Don't render if controllerData is null
  if (!controllerData) {
    return (
      <div className="w-full flex justify-center pt-6">
        <Card className="w-full min-h-[320px] min-w-[320px]">
          <CardContent>
            <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground">
                {getT(
                  "components.devices.controller_edit.loading_controller_data"
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full flex justify-center pt-6">
      <Card className="w-full min-h-[320px] min-w-[320px]">
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">
              {getT("components.devices.controller_edit.controller_details")}
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="type">
                {getT("components.devices.controller_edit.type")}
              </Label>
              <Input
                id="type"
                value={controllerData.type || ""}
                disabled={true}
                className="bg-muted"
              />
            </div>
            <div>
              <Label htmlFor="lan_ip_address">
                {getT("components.devices.controller_edit.ip_address")}
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
              <Label htmlFor="port_num">
                {getT("components.devices.controller_edit.port_number")}
              </Label>
              <Input
                id="port_num"
                name="port_num"
                type="number"
                value={formData.port_num}
                onChange={handleInputChange}
                disabled={!isEditing}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={toggleEditMode}
                  type="button"
                >
                  {getT("components.devices.controller_edit.cancel")}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={!isSaveEnabled || isLoading}
                >
                  {isLoading ? (
                    <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                  ) : null}
                  {isLoading
                    ? getT("components.devices.controller_edit.saving")
                    : getT("components.devices.controller_edit.save")}
                </Button>
              </>
            ) : (
              <Button onClick={toggleEditMode}>
                {getT("components.devices.controller_edit.edit")}
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
