import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

import { Skeleton } from "@/components/ui/skeleton";
import { Bridge, BridgeApiResponse, Controller, Port } from "@/lib/types";
import AddBridgeDialog from "./AddBridgeDialog";
import DeleteBridgeDialog from "./DeleteBridgeDialog";
import { toast } from "sonner";
import { Trash2, Loader2Icon } from "lucide-react";
import {
  deleteBridge,
  updateBridge,
  fetchControllers,
  fetchUnassignedPorts,
} from "@/lib/devices";
import { MultiSelect, MultiSelectOption } from "@/components/ui/multi-select";
import { useLanguage } from "@/context/languageContext";

export interface BridgeDataComponentProps {
  isLoading: boolean;
  bridgeData: BridgeApiResponse | null;
  deviceIp: string;
  fetchData: () => Promise<void>;
}

const BridgeDataComponent: React.FC<BridgeDataComponentProps> = ({
  isLoading,
  bridgeData,
  fetchData,
  deviceIp,
}) => {
  const { getT } = useLanguage();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaveEnabled, setIsSaveEnabled] = useState(false);
  const [isAddBridgeDialogOpen, setIsAddBridgeDialogOpen] = useState(false);
  const [isDeleteBridgeDialogOpen, setIsDeleteBridgeDialogOpen] =
    useState(false);
  const [bridgeToDelete, setBridgeToDelete] = useState<Bridge | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isLoadingUpdate, setIsLoadingUpdate] = useState(false);
  const [controllers, setControllers] = useState<Controller[]>([]);
  const [availablePorts, setAvailablePorts] = useState<MultiSelectOption[]>([]);
  const [formData, setFormData] = useState({
    id: 0,
    name: "",
    api_url: "",
    controller: null as Controller | null,
    controllerPort: 6653,
    ports: [] as Port[],
  });

  // Load controllers and available ports for the select dropdowns
  useEffect(() => {
    const loadData = async () => {
      try {
        const token = localStorage.getItem("taurineToken") || "";
        const [controllersData, portsData] = await Promise.all([
          fetchControllers(token),
          fetchUnassignedPorts(token, deviceIp),
        ]);
        setControllers(controllersData);

        // Get currently assigned ports from bridge data
        const currentPorts = bridgeData?.bridges?.[0]?.ports || [];
        const currentPortNames = currentPorts.map((port) => port.name);

        // Combine unassigned ports with currently assigned ports
        const allPortOptions: MultiSelectOption[] = [
          // Add currently assigned ports first
          ...currentPortNames.map((portName) => ({
            value: portName,
            label: portName,
          })),
          // Add unassigned ports
          ...(portsData.interfaces || [])
            .filter((port) => !currentPortNames.includes(port))
            .map((port) => ({
              value: port,
              label: port,
            })),
        ];

        setAvailablePorts(allPortOptions);
      } catch (error) {
        console.error("Error loading data:", error);
      }
    };
    loadData();
  }, [deviceIp, bridgeData]);

  // Update form data when bridge data changes
  useEffect(() => {
    if (bridgeData?.bridges && bridgeData.bridges.length > 0) {
      const bridge = bridgeData.bridges[0];
      setFormData({
        id: bridge.id,
        name: bridge.name || "",
        api_url: bridge.api_url || "",
        controller: bridge.controller || null,
        controllerPort: bridge.controller?.port_num || 6653,
        ports: bridge.ports || [],
      });
    }
  }, [bridgeData]);

  useEffect(() => {
    if (isEditing) {
      setIsSaveEnabled(hasChanges());
    } else {
      setIsSaveEnabled(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData, isEditing]);

  function hasChanges() {
    if (!bridgeData?.bridges || bridgeData.bridges.length === 0) return false;
    const bridge = bridgeData.bridges[0];
    return (
      formData.api_url !== bridge.api_url ||
      formData.controller?.id !== bridge.controller?.id ||
      formData.controllerPort !== bridge.controller?.port_num ||
      JSON.stringify(formData.ports.map((p) => p.name)) !==
        JSON.stringify(bridge.ports.map((p) => p.name))
    );
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  }

  function handleControllerChange(value: string) {
    if (value === "none") {
      setFormData((prev) => ({
        ...prev,
        controller: null,
        controllerPort: 6653,
      }));
    } else {
      const selectedController = controllers.find(
        (c) => c.id.toString() === value
      );
      setFormData((prev) => ({
        ...prev,
        controller: selectedController || null,
        controllerPort: selectedController?.port_num || 6653,
      }));
    }
  }

  function handlePortSelectionChange(selectedPortNames: string[]) {
    // Convert selected port names to Port objects
    const selectedPorts: Port[] = selectedPortNames.map((portName, index) => ({
      id: index + 1, // Temporary ID
      name: portName,
      device: 0, // Will be set by backend
      ovs_port_number: null,
      bridge: null,
    }));

    setFormData((prev) => ({
      ...prev,
      ports: selectedPorts,
    }));
  }

  function toggleEditMode() {
    setIsEditing((editing) => !editing);
    if (isEditing) {
      // Reset form data to original values
      if (bridgeData?.bridges && bridgeData.bridges.length > 0) {
        const bridge = bridgeData.bridges[0];
        setFormData({
          id: bridge.id,
          name: bridge.name || "",
          api_url: bridge.api_url || "",
          controller: bridge.controller || null,
          controllerPort: bridge.controller?.port_num || 6653,
          ports: bridge.ports || [],
        });
      }
    }
  }

  async function handleSave() {
    if (!hasChanges()) {
      setIsEditing(false);
      return;
    }
    setIsLoadingUpdate(true);
    try {
      const token = localStorage.getItem("taurineToken") || "";

      const updateData = {
        id: formData.id,
        name: formData.name,
        api_url: formData.api_url,
        controller: formData.controller,
        controller_port: formData.controllerPort,
        ports: formData.ports.map((p) => p.name),
        lan_ip_address: deviceIp,
      } as unknown as Partial<Bridge>;

      await updateBridge(token, updateData);
      setIsEditing(false);
      toast.success(getT("components.devices.bridge_data.success"));
      await fetchData();
    } catch (error) {
      console.error("Error updating bridge:", error);
      toast.error(getT("components.devices.bridge_data.error"));
    } finally {
      setIsLoadingUpdate(false);
    }
  }

  const handleAddBridgeClick = () => {
    setIsAddBridgeDialogOpen(true);
  };

  const handleAddBridgeDialogClose = () => {
    setIsAddBridgeDialogOpen(false);
  };

  const handleBridgeAdded = async () => {
    await fetchData();
    setIsAddBridgeDialogOpen(false);
  };

  const handleBridgeSuccess = (message: string) => {
    toast.success(message);
  };

  const handleBridgeError = (message: string) => {
    toast.error(message);
  };

  const handleQosSuccess = async (message: string) => {
    toast.success(message);
  };

  const handleQosError = (message: string) => {
    toast.warning(message);
  };

  const handleDeleteBridgeClick = (bridge: Bridge) => {
    setBridgeToDelete(bridge);
    setIsDeleteBridgeDialogOpen(true);
  };

  const handleDeleteBridgeDialogClose = () => {
    setIsDeleteBridgeDialogOpen(false);
    setBridgeToDelete(null);
  };

  const handleDeleteBridge = async () => {
    setIsDeleting(true);

    try {
      const token = localStorage.getItem("taurineToken") || "";
      const bridgeData = {
        name: bridgeToDelete?.name || "",
        lan_ip_address: deviceIp,
      };

      await deleteBridge(token, bridgeData);
      await fetchData();
      toast.success(getT("components.devices.bridge_data.delete_success"));
    } catch (error) {
      console.error("Error deleting bridge:", error);

      const errorMessage =
        error instanceof Error && "response" in error
          ? (error as { response?: { data?: { message?: string } } }).response
              ?.data?.message ||
            getT("components.devices.bridge_data.delete_error")
          : getT("components.devices.bridge_data.delete_error");
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
      setIsDeleteBridgeDialogOpen(false);
      setBridgeToDelete(null);
    }
  };

  if (isLoading || isDeleting) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{getT("components.devices.bridge_data.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center">
            <Skeleton className="h-6 w-full mb-2 bg-muted" />
            <Skeleton className="h-6 w-full mb-2 bg-muted" />
            <Skeleton className="h-6 w-full mb-2 bg-muted" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!bridgeData?.bridges || bridgeData.bridges.length === 0) {
    return (
      <>
        <Card className="w-full">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>
              {getT("components.devices.bridge_data.title")}
            </CardTitle>
            <Button
              size="sm"
              onClick={handleAddBridgeClick}
              disabled={isLoading || isDeleting}
            >
              {getT("components.devices.bridge_data.add_bridge")}
            </Button>
          </CardHeader>
          <CardContent>
            <div className="text-muted-foreground">
              {getT("components.devices.bridge_data.no_bridges")}
            </div>
          </CardContent>
        </Card>

        <AddBridgeDialog
          isOpen={isAddBridgeDialogOpen}
          onClose={handleAddBridgeDialogClose}
          deviceIp={deviceIp}
          onBridgeAdded={handleBridgeAdded}
          onBridgeSuccess={handleBridgeSuccess}
          onBridgeError={handleBridgeError}
          onQosSuccess={handleQosSuccess}
          onQosError={handleQosError}
        />
      </>
    );
  }

  const bridge = bridgeData.bridges[0];

  return (
    <>
      <Card className="w-full">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{getT("components.devices.bridge_data.title")}</CardTitle>
          <div className="flex gap-2">
            {isEditing ? (
              <>
                <Button
                  variant="outline"
                  onClick={toggleEditMode}
                  type="button"
                  size="sm"
                  disabled={isLoadingUpdate}
                >
                  {getT("components.devices.bridge_data.cancel")}
                </Button>
                <Button
                  onClick={handleSave}
                  disabled={!isSaveEnabled || isLoadingUpdate}
                  size="sm"
                >
                  {isLoadingUpdate ? (
                    <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                  ) : null}
                  {getT("components.devices.bridge_data.save")}
                </Button>
              </>
            ) : (
              <>
                <Button onClick={toggleEditMode} size="sm">
                  {getT("components.devices.bridge_data.edit")}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteBridgeClick(bridge)}
                  className="h-8 w-8 p-0 text-destructive hover:text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <Label htmlFor="name">Bridge Name (Read-only)</Label>
              <Input
                id="name"
                value={bridge.name}
                disabled={true}
                className="bg-muted"
              />
            </div>
            <div>
              <Label htmlFor="dpid">DPID (Read-only)</Label>
              <Input
                id="dpid"
                value={bridge.dpid}
                disabled={true}
                className="bg-muted"
              />
            </div>
            <div>
              <Label htmlFor="odl_node_id">ODL Node ID (Read-only)</Label>
              <Input
                id="odl_node_id"
                value={bridge.odl_node_id || "N/A"}
                disabled={true}
                className="bg-muted"
              />
            </div>
            <div>
              <Label htmlFor="api_url">API URL</Label>
              <Input
                id="api_url"
                name="api_url"
                value={formData.api_url}
                onChange={handleInputChange}
                disabled={!isEditing || isLoadingUpdate}
              />
            </div>
            <div>
              <Label htmlFor="controller">Controller</Label>
              <Select
                value={formData.controller?.id?.toString() || "none"}
                onValueChange={handleControllerChange}
                disabled={!isEditing || isLoadingUpdate}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Controller" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Controller</SelectItem>
                  {controllers.map((controller) => (
                    <SelectItem
                      key={controller.id}
                      value={controller.id.toString()}
                    >
                      {controller.type.toUpperCase()} -{" "}
                      {controller.lan_ip_address}:{controller.port_num}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {formData.controller && (
              <div>
                <Label htmlFor="controller_port">Controller Port</Label>
                <Input
                  id="controller_port"
                  name="controllerPort"
                  type="number"
                  value={formData.controllerPort}
                  onChange={handleInputChange}
                  disabled={!isEditing || isLoadingUpdate}
                />
              </div>
            )}
            <div className="md:col-span-2">
              <Label htmlFor="ports">Ports</Label>
              <MultiSelect
                options={availablePorts}
                selectedValues={formData.ports.map((p) => p.name)}
                onSelectionChange={handlePortSelectionChange}
                placeholder="Select ports..."
                searchPlaceholder="Search ports..."
                emptyMessage="No ports available"
                disabled={!isEditing || isLoadingUpdate}
                maxDisplayed={5}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <AddBridgeDialog
        isOpen={isAddBridgeDialogOpen}
        onClose={handleAddBridgeDialogClose}
        deviceIp={deviceIp}
        onBridgeAdded={handleBridgeAdded}
        onBridgeSuccess={handleBridgeSuccess}
        onBridgeError={handleBridgeError}
        onQosSuccess={handleQosSuccess}
        onQosError={handleQosError}
      />

      {bridgeToDelete && (
        <DeleteBridgeDialog
          isOpen={isDeleteBridgeDialogOpen}
          onClose={handleDeleteBridgeDialogClose}
          bridgeName={bridgeToDelete.name}
          handleDelete={handleDeleteBridge}
          isDeleting={isDeleting}
        />
      )}
    </>
  );
};

export default BridgeDataComponent;
