//TODO: fix the weird behavior of the form when editing and reduce useEffect and useMemo calls. Address: select.tsx:12 Select is changing from uncontrolled to controlled.

"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2, Edit, Trash2, Network, Save, X } from "lucide-react";
import {
  PluginInstallation,
  SnifferInstallationConfig,
  Bridge,
  Port,
} from "@/lib/types";
import { deleteSnifferInstallation, updateSnifferConfig } from "@/lib/software";
import { fetchBridges } from "@/lib/devices";
import { validateApiUrl } from "@/lib/utils";
import { useAuth } from "@/context/authContext";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";

interface SnifferInstallationListProps {
  installations: PluginInstallation[];
  onRefresh: () => void;
}

interface InstallationData {
  installation: PluginInstallation;
  bridges: Bridge[];
  ports: Port[];
  isLoading: boolean;
  isLoaded: boolean;
}

export function SnifferInstallationList({
  installations,
  onRefresh,
}: SnifferInstallationListProps) {
  const { token } = useAuth();
  const { getT } = useLanguage();
  const [isDeleting, setIsDeleting] = useState(false);
  const [installationToDelete, setInstallationToDelete] =
    useState<PluginInstallation | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [editingInstallation, setEditingInstallation] =
    useState<PluginInstallation | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [formData, setFormData] = useState({
    api_base_url: "",
    monitor_interface: "",
    port_to_client: "",
    port_to_router: "",
    bridge_name: "",
  });

  // Data state for each installation
  const [installationsData, setInstallationsData] = useState<
    InstallationData[]
  >([]);

  // Error state
  const [portSelectionError, setPortSelectionError] = useState("");
  const [apiUrlError, setApiUrlError] = useState("");

  // Filter for sniffer installations
  const snifferInstallations = useMemo(() => {
    return installations.filter(
      (inst) =>
        inst.plugin?.name === "tau-traffic-classification-sniffer" &&
        inst.sniffer_config
    );
  }, [installations]);

  // Initialize installations data
  useEffect(() => {
    if (!token || snifferInstallations.length === 0) return;

    const initializeData = async () => {
      const newInstallationsData: InstallationData[] = snifferInstallations.map(
        (installation) => ({
          installation,
          bridges: [],
          ports: [],
          isLoading: false,
          isLoaded: false,
        })
      );

      setInstallationsData(newInstallationsData);

      // Load data for each installation
      for (let index = 0; index < newInstallationsData.length; index++) {
        const data = newInstallationsData[index];
        if (!data.installation.device?.id || !token) continue;

        setInstallationsData((prev) =>
          prev.map((item, i) =>
            i === index ? { ...item, isLoading: true } : item
          )
        );

        try {
          const bridgesData = await fetchBridges(
            token,
            data.installation.device!.id.toString()
          );
          const bridges = bridgesData.bridges as Bridge[];

          // Find the current bridge and get its ports
          const currentBridge = bridges.find(
            (bridge) =>
              bridge.name === data.installation.sniffer_config?.bridge_name
          );
          const ports = currentBridge?.ports || [];

          setInstallationsData((prev) =>
            prev.map((item, i) =>
              i === index
                ? {
                    ...item,
                    bridges,
                    ports,
                    isLoading: false,
                    isLoaded: true,
                  }
                : item
            )
          );
        } catch (err) {
          console.error("Error loading data for installation:", err);
          setInstallationsData((prev) =>
            prev.map((item, i) =>
              i === index ? { ...item, isLoading: false, isLoaded: true } : item
            )
          );
        }
      }
    };

    initializeData();
  }, [snifferInstallations, token]);

  // Update form data when editing installation changes
  useEffect(() => {
    if (editingInstallation?.sniffer_config) {
      const config = editingInstallation.sniffer_config;
      setFormData({
        api_base_url: config.api_base_url || "",
        monitor_interface: config.monitor_interface || "",
        port_to_client: config.port_to_client || "",
        port_to_router: config.port_to_router || "",
        bridge_name: config.bridge_name || "",
      });
    }
  }, [editingInstallation?.id, editingInstallation?.sniffer_config]);

  // Update ports when bridge selection changes
  useEffect(() => {
    if (!editingInstallation?.id || !formData.bridge_name) return;

    setInstallationsData((prev) =>
      prev.map((item) => {
        if (item.installation.id === editingInstallation.id) {
          const selectedBridge = item.bridges.find(
            (bridge) => bridge.name === formData.bridge_name
          );
          const newPorts = selectedBridge?.ports || [];
          return { ...item, ports: newPorts };
        }
        return item;
      })
    );
  }, [formData.bridge_name, editingInstallation?.id]);

  const hasChanges = () => {
    if (!editingInstallation?.sniffer_config) return false;
    const config = editingInstallation.sniffer_config;
    return (
      formData.api_base_url !== config.api_base_url ||
      formData.monitor_interface !== config.monitor_interface ||
      formData.port_to_client !== config.port_to_client ||
      formData.port_to_router !== config.port_to_router ||
      formData.bridge_name !== config.bridge_name
    );
  };

  // Memoize form data to prevent unnecessary re-renders
  const memoizedFormData = useMemo(() => formData, [formData]);

  // Form validation
  const isFormValid =
    memoizedFormData.api_base_url.trim() &&
    !apiUrlError &&
    memoizedFormData.bridge_name &&
    memoizedFormData.monitor_interface &&
    memoizedFormData.port_to_client &&
    memoizedFormData.port_to_router &&
    memoizedFormData.port_to_client !== memoizedFormData.port_to_router;

  // Validate port selection
  useEffect(() => {
    if (
      memoizedFormData.port_to_client &&
      memoizedFormData.port_to_router &&
      memoizedFormData.port_to_client === memoizedFormData.port_to_router
    ) {
      setPortSelectionError(
        getT("components.plugins.sniffer_install_form.port_selection_error")
      );
    } else {
      setPortSelectionError("");
    }
  }, [memoizedFormData.port_to_client, memoizedFormData.port_to_router, getT]);

  // Validate API URL
  useEffect(() => {
    const error = validateApiUrl(memoizedFormData.api_base_url);
    setApiUrlError(error);
  }, [memoizedFormData.api_base_url]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const startEditing = (installation: PluginInstallation) => {
    setEditingInstallation(installation);
  };

  const cancelEditing = () => {
    setEditingInstallation(null);
    setFormData({
      api_base_url: "",
      monitor_interface: "",
      port_to_client: "",
      port_to_router: "",
      bridge_name: "",
    });
  };

  const handleSave = async () => {
    if (!editingInstallation?.sniffer_config || !token) return;
    setIsUpdating(true);
    try {
      await updateSnifferConfig(token, editingInstallation.id, formData);
      toast.success(
        getT("components.plugins.sniffer_installation_list.update_success")
      );
      onRefresh();
      setEditingInstallation(null);
    } catch (err) {
      console.error("Failed to update sniffer configuration:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : getT("components.plugins.sniffer_installation_list.update_error");
      toast.error(errorMessage);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!installationToDelete || !token) return;

    setIsDeleting(true);

    try {
      await deleteSnifferInstallation(token, installationToDelete.id);
      toast.success(
        getT("components.plugins.sniffer_installation_list.delete_success")
      );
      onRefresh();
      setIsDeleteDialogOpen(false);
      setInstallationToDelete(null);
    } catch (err) {
      console.error("Failed to delete sniffer installation:", err);
      const errorMessage =
        err instanceof Error
          ? err.message
          : getT("components.plugins.sniffer_installation_list.delete_error");
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  const openDeleteDialog = (installation: PluginInstallation) => {
    setInstallationToDelete(installation);
    setIsDeleteDialogOpen(true);
  };

  const closeDeleteDialog = () => {
    setIsDeleteDialogOpen(false);
    setInstallationToDelete(null);
  };

  if (snifferInstallations.length === 0) {
    return (
      <div className="text-center py-12">
        <Network className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">
          {getT(
            "components.plugins.sniffer_installation_list.no_installations"
          )}
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">
            {getT("components.plugins.sniffer_installation_list.title")}
          </h3>
          <span className="text-sm text-muted-foreground">
            {snifferInstallations.length}{" "}
            {getT("components.plugins.sniffer_installation_list.installed")}
          </span>
        </div>

        <div className="grid gap-4">
          {installationsData.map((data) => {
            const { installation, bridges, ports, isLoading, isLoaded } = data;
            const config =
              installation.sniffer_config as SnifferInstallationConfig;
            const isEditing = editingInstallation?.id === installation.id;

            return (
              <Card
                key={installation.id}
                className="relative flex flex-col h-full"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">
                        {installation.device?.name ||
                          getT(
                            "components.plugins.sniffer_installation_list.unknown_device"
                          )}
                      </CardTitle>
                      <CardDescription>
                        {installation.device?.lan_ip_address ||
                          getT(
                            "components.plugins.sniffer_installation_list.no_ip_address"
                          )}
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      {isEditing ? (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={cancelEditing}
                            disabled={isUpdating}
                          >
                            <X className="w-4 h-4 mr-2" />
                            {getT(
                              "components.plugins.sniffer_installation_list.cancel"
                            )}
                          </Button>
                          <Button
                            onClick={handleSave}
                            disabled={
                              !isFormValid || isUpdating || !hasChanges()
                            }
                            size="sm"
                          >
                            {isUpdating && (
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            )}
                            <Save className="w-4 h-4 mr-2" />
                            {getT(
                              "components.plugins.sniffer_installation_list.save"
                            )}
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => startEditing(installation)}
                            disabled={isUpdating || !isLoaded}
                          >
                            {isLoading ? (
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                              <Edit className="w-4 h-4 mr-2" />
                            )}
                            {isLoading
                              ? getT(
                                  "components.plugins.sniffer_installation_list.loading"
                                )
                              : getT(
                                  "components.plugins.sniffer_installation_list.edit"
                                )}
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => openDeleteDialog(installation)}
                            disabled={isUpdating}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            {getT(
                              "components.plugins.sniffer_installation_list.delete"
                            )}
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-0 flex-1">
                  <div className="grid gap-4">
                    {/* Device and Installation Date (Read-only) */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          {getT(
                            "components.plugins.sniffer_installation_list.device_ip_readonly"
                          )}
                        </Label>
                        <Input
                          value={
                            installation.device?.lan_ip_address ||
                            getT(
                              "components.plugins.sniffer_installation_list.not_set"
                            )
                          }
                          disabled={true}
                          className="bg-muted"
                        />
                      </div>
                      <div>
                        <Label className="text-sm font-medium text-muted-foreground">
                          {getT(
                            "components.plugins.sniffer_installation_list.installed_date_readonly"
                          )}
                        </Label>
                        <Input
                          value={new Date(
                            installation.installed_at
                          ).toLocaleString()}
                          disabled={true}
                          className="bg-muted"
                        />
                      </div>
                    </div>

                    {/* Editable Configuration Fields */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor={`api-url-${installation.id}`}>
                          {getT(
                            "components.plugins.sniffer_installation_list.api_url"
                          )}
                        </Label>
                        <Input
                          id={`api-url-${installation.id}`}
                          name="api_base_url"
                          value={
                            isEditing
                              ? memoizedFormData.api_base_url
                              : config.api_base_url ||
                                getT(
                                  "components.plugins.sniffer_installation_list.not_set"
                                )
                          }
                          onChange={handleInputChange}
                          disabled={!isEditing || isUpdating}
                          placeholder={getT(
                            "components.plugins.sniffer_installation_list.api_url_placeholder"
                          )}
                        />
                        {isEditing && apiUrlError && (
                          <p className="text-sm text-destructive">
                            {apiUrlError}
                          </p>
                        )}
                      </div>
                      <div>
                        <Label htmlFor={`bridge-name-${installation.id}`}>
                          {getT(
                            "components.plugins.sniffer_installation_list.bridge_name"
                          )}
                        </Label>
                        {isEditing ? (
                          <Select
                            onValueChange={(value) =>
                              setFormData((prev) => ({
                                ...prev,
                                bridge_name: value,
                              }))
                            }
                            value={memoizedFormData.bridge_name || undefined}
                            disabled={isUpdating}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue
                                placeholder={getT(
                                  "components.plugins.sniffer_installation_list.select_bridge"
                                )}
                              />
                            </SelectTrigger>
                            <SelectContent>
                              {bridges.length === 0 ? (
                                <SelectItem value="no-bridges" disabled>
                                  {getT(
                                    "components.plugins.sniffer_installation_list.no_bridges_found"
                                  )}
                                </SelectItem>
                              ) : (
                                bridges
                                  .filter(
                                    (bridge) =>
                                      bridge.name && bridge.name.trim() !== ""
                                  )
                                  .map((bridge) => (
                                    <SelectItem
                                      key={bridge.name}
                                      value={bridge.name}
                                    >
                                      {bridge.name}
                                    </SelectItem>
                                  ))
                              )}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={
                              config.bridge_name ||
                              getT(
                                "components.plugins.sniffer_installation_list.not_set"
                              )
                            }
                            disabled={true}
                            className="bg-muted"
                          />
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor={`monitor-interface-${installation.id}`}>
                          {getT(
                            "components.plugins.sniffer_installation_list.monitor_interface"
                          )}
                        </Label>
                        {isEditing ? (
                          <Select
                            onValueChange={(value) =>
                              setFormData((prev) => ({
                                ...prev,
                                monitor_interface: value,
                              }))
                            }
                            value={
                              memoizedFormData.monitor_interface || undefined
                            }
                            disabled={
                              isUpdating || !memoizedFormData.bridge_name
                            }
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue
                                placeholder={getT(
                                  "components.plugins.sniffer_installation_list.select_monitoring_interface"
                                )}
                              />
                            </SelectTrigger>
                            <SelectContent>
                              {ports.length === 0 ? (
                                <SelectItem value="no-ports" disabled>
                                  {getT(
                                    "components.plugins.sniffer_installation_list.no_ports_available"
                                  )}
                                </SelectItem>
                              ) : (
                                ports
                                  .filter(
                                    (port) =>
                                      port.name && port.name.trim() !== ""
                                  )
                                  .map((port) => (
                                    <SelectItem
                                      key={port.name}
                                      value={port.name}
                                    >
                                      {port.name} (OVS Port:{" "}
                                      {port.ovs_port_number})
                                    </SelectItem>
                                  ))
                              )}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={
                              config.monitor_interface ||
                              getT(
                                "components.plugins.sniffer_installation_list.not_set"
                              )
                            }
                            disabled={true}
                            className="bg-muted"
                          />
                        )}
                      </div>
                      <div>
                        <Label htmlFor={`client-port-${installation.id}`}>
                          {getT(
                            "components.plugins.sniffer_installation_list.client_port"
                          )}
                        </Label>
                        {isEditing ? (
                          <Select
                            onValueChange={(value) =>
                              setFormData((prev) => ({
                                ...prev,
                                port_to_client: value,
                              }))
                            }
                            value={memoizedFormData.port_to_client || undefined}
                            disabled={
                              isUpdating || !memoizedFormData.bridge_name
                            }
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue
                                placeholder={getT(
                                  "components.plugins.sniffer_installation_list.select_client_port"
                                )}
                              />
                            </SelectTrigger>
                            <SelectContent>
                              {ports.length === 0 ? (
                                <SelectItem value="no-ports" disabled>
                                  {getT(
                                    "components.plugins.sniffer_installation_list.no_ports_available"
                                  )}
                                </SelectItem>
                              ) : (
                                ports
                                  .filter(
                                    (port) => port.ovs_port_number != null
                                  )
                                  .filter(
                                    (port) =>
                                      port.name && port.name.trim() !== ""
                                  )
                                  .map((port) => (
                                    <SelectItem
                                      key={port.ovs_port_number!.toString()}
                                      value={port.ovs_port_number!.toString()}
                                    >
                                      {port.name} (OVS Port:{" "}
                                      {port.ovs_port_number})
                                    </SelectItem>
                                  ))
                              )}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={
                              config.port_to_client ||
                              getT(
                                "components.plugins.sniffer_installation_list.not_set"
                              )
                            }
                            disabled={true}
                            className="bg-muted"
                          />
                        )}
                      </div>
                      <div>
                        <Label htmlFor={`wan-port-${installation.id}`}>
                          {getT(
                            "components.plugins.sniffer_installation_list.wan_port"
                          )}
                        </Label>
                        {isEditing ? (
                          <Select
                            onValueChange={(value) =>
                              setFormData((prev) => ({
                                ...prev,
                                port_to_router: value,
                              }))
                            }
                            value={memoizedFormData.port_to_router || undefined}
                            disabled={
                              isUpdating || !memoizedFormData.bridge_name
                            }
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue
                                placeholder={getT(
                                  "components.plugins.sniffer_installation_list.select_wan_port"
                                )}
                              />
                            </SelectTrigger>
                            <SelectContent>
                              {ports.length === 0 ? (
                                <SelectItem value="no-ports" disabled>
                                  {getT(
                                    "components.plugins.sniffer_installation_list.no_ports_available"
                                  )}
                                </SelectItem>
                              ) : (
                                ports
                                  .filter(
                                    (port) => port.ovs_port_number != null
                                  )
                                  .filter(
                                    (port) =>
                                      port.name && port.name.trim() !== ""
                                  )
                                  .map((port) => (
                                    <SelectItem
                                      key={port.ovs_port_number!.toString()}
                                      value={port.ovs_port_number!.toString()}
                                    >
                                      {port.name} (OVS Port:{" "}
                                      {port.ovs_port_number})
                                    </SelectItem>
                                  ))
                              )}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            value={
                              config.port_to_router ||
                              getT(
                                "components.plugins.sniffer_installation_list.not_set"
                              )
                            }
                            disabled={true}
                            className="bg-muted"
                          />
                        )}
                      </div>
                    </div>

                    {isEditing && portSelectionError && (
                      <div className="text-sm text-destructive">
                        {portSelectionError}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {getT(
                "components.plugins.sniffer_installation_list.confirm_deletion"
              )}
            </DialogTitle>
            <DialogDescription>
              {getT(
                "components.plugins.sniffer_installation_list.delete_confirmation_message",
                `Are you sure you want to delete the sniffer installation on device ${
                  installationToDelete?.device?.lan_ip_address || "N/A"
                }? This action cannot be undone.`
              )}
            </DialogDescription>
          </DialogHeader>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={closeDeleteDialog}
              disabled={isDeleting}
            >
              {getT("components.plugins.sniffer_installation_list.cancel")}
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={isDeleting}
            >
              {isDeleting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isDeleting
                ? getT("components.plugins.sniffer_installation_list.deleting")
                : getT("components.plugins.sniffer_installation_list.delete")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
