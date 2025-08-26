"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
} from "@/components/ui/breadcrumb";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CreateMeterDialog } from "@/components/meters/CreateMeterDialog";
import { ManageCategoriesDialog } from "@/components/meters/ManageCategoriesDialog";
import { ConfirmDeleteMeterDialog } from "@/components/meters/ConfirmDeleteMeterDialog";
import { SwitchTabs } from "@/components/meters/SwitchTabs";
import {
  fetchOdlControllers,
  fetchOdlControllerNodes,
  fetchOdlMetersForSwitch,
  odlDeleteMeter,
} from "@/lib/odl";
import { fetchCategories } from "@/lib/classifier";
import {
  OdlController,
  OdlNode,
  OdlMeter,
  AlertState,
  DialogState,
  LoadingState,
} from "@/lib/types";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";
import { useModel } from "@/context/ModelContext";
import { ModelSelectionComponent } from "@/components/meters/ModelSelectionComponent";

export default function TauOdlMetreTrafficClassification() {
  const { getT } = useLanguage();
  const { activeModel } = useModel();

  // State management
  const [controllers, setControllers] = useState<OdlController[]>([]);
  const [selectedController, setSelectedController] =
    useState<OdlController | null>(null);
  const [nodes, setNodes] = useState<OdlNode[]>([]);
  const [meters, setMeters] = useState<OdlMeter[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");

  // Loading states
  const [loading, setLoading] = useState<LoadingState>({
    isLoading: true,
    isLoadingNodes: false,
    isLoadingMeters: false,
  });

  // Alert state
  const [alert, setAlert] = useState<AlertState>({
    message: "",
    severity: "success",
    show: false,
  });

  // Dialog states
  const [dialog, setDialog] = useState<DialogState>({
    isCreateDialogOpen: false,
    isCategoriesDialogOpen: false,
    isDeleteDialogOpen: false,
    currentNodeOdlId: "",
    currentMeter: null,
    macAddress: "",
  });

  const handleAlert = useCallback(
    (severity: AlertState["severity"] = "success", message: string = "") => {
      setAlert({
        message,
        severity,
        show: message !== "",
      });
    },
    []
  );

  const getOdlControllersList = useCallback(async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      const odlControllerData = await fetchOdlControllers(token);
      setControllers(odlControllerData || []);
      if (odlControllerData && odlControllerData.length > 0) {
        setSelectedController(odlControllerData[0]);
      } else {
        setSelectedController(null);
        setNodes([]);
        setMeters([]);
      }
    } catch (error: unknown) {
      console.error("Error fetching ODL controllers:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Error fetching controllers";
      handleAlert("error", errorMessage);
      setControllers([]);
      setSelectedController(null);
    }
  }, [handleAlert]);

  const getNodesForController = useCallback(
    async (controllerDbId: number) => {
      if (!controllerDbId) {
        setNodes([]);
        setMeters([]);
        return;
      }

      const token = localStorage.getItem("taurineToken");
      if (!token) return;

      setLoading((prev) => ({ ...prev, isLoadingNodes: true }));

      try {
        const controllerNodesData = await fetchOdlControllerNodes(
          token,
          controllerDbId
        );
        setNodes(controllerNodesData || []);
        setMeters([]); // Clear existing meters when nodes change

        if (controllerNodesData && controllerNodesData.length > 0) {
          // We'll handle meter fetching separately to avoid circular dependencies
          // await fetchAllMetersForNodes(
          //   selectedController?.lan_ip_address || "",
          //   controllerNodesData
          // );
        }
      } catch (error: unknown) {
        console.error("Error fetching ODL nodes:", error);
        const errorMessage =
          error instanceof Error ? error.message : "Error fetching nodes";
        handleAlert("error", errorMessage);
        setNodes([]);
        setMeters([]);
      } finally {
        setLoading((prev) => ({ ...prev, isLoadingNodes: false }));
      }
    },
    [handleAlert]
  );

  const getMetersForNode = useCallback(
    async (controllerIp: string, switchNodeId: string): Promise<OdlMeter[]> => {
      try {
        const token = localStorage.getItem("taurineToken");
        if (!token) return [];

        const metersList = await fetchOdlMetersForSwitch(
          token,
          controllerIp,
          switchNodeId,
          selectedModel || activeModel?.name
        );
        return metersList;
      } catch (error: unknown) {
        console.error("Error fetching meters for node:", error);
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch meters";
        handleAlert("error", errorMessage);
        return [];
      }
    },
    [handleAlert, selectedModel, activeModel]
  );

  const fetchAllMetersForNodes = useCallback(
    async (controllerIp: string, currentNodes: OdlNode[]) => {
      try {
        setLoading((prev) => ({ ...prev, isLoadingMeters: true }));
        const allMeters: OdlMeter[] = [];

        for (const node of currentNodes) {
          const nodeMeters = await getMetersForNode(
            controllerIp,
            node.odl_node_id
          );
          allMeters.push(...nodeMeters);
        }

        setMeters(allMeters);
      } catch (error: unknown) {
        console.error("Error fetching all meters:", error);
        const errorMessage =
          error instanceof Error ? error.message : "Failed to fetch meters";
        handleAlert("error", errorMessage);
      } finally {
        setLoading((prev) => ({ ...prev, isLoadingMeters: false }));
      }
    },
    [getMetersForNode, handleAlert]
  );

  const getCategoriesList = useCallback(async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    try {
      const categoryRsp = await fetchCategories(
        token,
        selectedModel || activeModel?.name
      );
      setCategories(categoryRsp.categories || []);
    } catch (error: unknown) {
      console.error("Error fetching categories:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Error fetching categories";
      handleAlert("error", errorMessage);
    }
  }, [handleAlert, selectedModel, activeModel]);

  // Initial data load
  useEffect(() => {
    const getData = async () => {
      setLoading((prev) => ({ ...prev, isLoading: true }));
      await getCategoriesList();
      await getOdlControllersList();
      setLoading((prev) => ({ ...prev, isLoading: false }));
    };
    getData();
  }, [getCategoriesList, getOdlControllersList]);

  // Effect for when selectedController changes
  useEffect(() => {
    if (selectedController) {
      getNodesForController(selectedController.id);
    } else {
      setNodes([]);
      setMeters([]);
    }
  }, [selectedController, getNodesForController]);

  // Effect for when nodes change, fetch meters for the new nodes
  useEffect(() => {
    if (selectedController && nodes.length > 0) {
      fetchAllMetersForNodes(selectedController.lan_ip_address, nodes);
    }
  }, [selectedController, nodes, fetchAllMetersForNodes]);

  // Effect for when model changes, refresh categories and meters
  useEffect(() => {
    if (selectedController) {
      getCategoriesList();
      if (nodes.length > 0) {
        fetchAllMetersForNodes(selectedController.lan_ip_address, nodes);
      }
    }
  }, [
    selectedModel,
    activeModel,
    getCategoriesList,
    fetchAllMetersForNodes,
    selectedController,
    nodes,
  ]);

  // Dialog handlers
  const handleOpenCreateDialog = (nodeOdlId: string) => {
    setDialog((prev) => ({
      ...prev,
      currentNodeOdlId: nodeOdlId,
      isCreateDialogOpen: true,
    }));
  };

  const handleCloseCreateDialog = async (success: boolean) => {
    setDialog((prev) => ({ ...prev, isCreateDialogOpen: false }));

    if (success && selectedController && dialog.currentNodeOdlId) {
      await fetchAllMetersForNodes(selectedController.lan_ip_address, nodes);
    }

    setDialog((prev) => ({ ...prev, currentNodeOdlId: "" }));
  };

  const handleOpenCategoriesDialog = (
    meter: OdlMeter,
    nodeOdlId: string,
    meterMacAddress: string
  ) => {
    setDialog((prev) => ({
      ...prev,
      currentMeter: meter,
      currentNodeOdlId: nodeOdlId,
      macAddress: meterMacAddress,
      isCategoriesDialogOpen: true,
    }));
  };

  const handleCloseCategoriesDialog = async (success: boolean) => {
    setDialog((prev) => ({ ...prev, isCategoriesDialogOpen: false }));

    if (success && selectedController && dialog.currentMeter?.switch_node_id) {
      await fetchAllMetersForNodes(selectedController.lan_ip_address, nodes);
    }
  };

  const handlePressDeleteMeter = (meter: OdlMeter, nodeOdlId: string) => {
    setDialog((prev) => ({
      ...prev,
      currentMeter: meter,
      currentNodeOdlId: nodeOdlId,
      isDeleteDialogOpen: true,
    }));
  };

  const handleDeleteMeter = async () => {
    if (!dialog.currentMeter?.id) return;

    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) return;

      await odlDeleteMeter(token, dialog.currentMeter.id);
      toast.success(
        getT(
          "components.meters.meter_deleted_success",
          "Meter deleted successfully"
        )
      );
      setDialog((prev) => ({ ...prev, isDeleteDialogOpen: false }));

      // Refetch meters for the affected node
      if (selectedController && dialog.currentMeter.switch_node_id) {
        const newMetersForNode = await getMetersForNode(
          selectedController.lan_ip_address,
          dialog.currentMeter.switch_node_id
        );
        setMeters((prevMeters) => {
          const otherNodeMeters = prevMeters.filter(
            (m) => m.switch_node_id !== dialog.currentMeter?.switch_node_id
          );
          return [...otherNodeMeters, ...newMetersForNode];
        });
      }
    } catch (error: unknown) {
      console.error("Error deleting ODL meter:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete meter";
      toast.error(errorMessage);
    }
  };

  const handleCloseDeleteDialog = () => {
    setDialog((prev) => ({ ...prev, isDeleteDialogOpen: false }));
  };

  return (
    <ProtectedRoute>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator
                orientation="vertical"
                className="mr-2 data-[orientation=vertical]:h-4"
              />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/plugins">
                      {getT("navigation.plugins", "Plugins")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>

          <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
            <div className="w-full flex flex-row items-end justify-between mb-6">
              <h1 className="text-2xl font-bold text-muted-foreground">
                {getT(
                  "page.TauOdlMetreTrafficClassification.page_title",
                  "Traffic Classification Rules"
                )}
              </h1>
            </div>

            {alert.show && (
              <Alert
                variant={alert.severity === "error" ? "destructive" : "default"}
              >
                <AlertDescription>{alert.message}</AlertDescription>
              </Alert>
            )}

            {loading.isLoading ? (
              <div className="flex justify-center items-center h-50vh">
                <div className="space-y-4">
                  <Skeleton className="h-8 w-[200px]" />
                  <Skeleton className="h-4 w-[300px]" />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-6">
                {/* Model Selection */}
                <ModelSelectionComponent
                  selectedModel={selectedModel}
                  onModelChange={setSelectedModel}
                  showActiveIndicator={true}
                  showModelDetails={true}
                  className="w-full"
                />

                {controllers.length > 0 && selectedController ? (
                  <Card className="w-full ">
                    <CardHeader>
                      <CardTitle>
                        {getT(
                          "components.meters.select_controller",
                          "Select Controller"
                        )}
                      </CardTitle>
                      <CardDescription>
                        {getT(
                          "components.meters.select_controller_description",
                          "Choose an OpenDaylight controller to manage its meters"
                        )}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Select
                        value={selectedController.id.toString()}
                        onValueChange={(value) => {
                          const newSelectedController = controllers.find(
                            (ctrl) => ctrl.id.toString() === value
                          );
                          handleAlert("success", ""); // Clear previous alerts
                          setSelectedController(newSelectedController || null);
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue
                            placeholder={getT(
                              "components.meters.select_controller_placeholder",
                              "Select a controller"
                            )}
                          />
                        </SelectTrigger>
                        <SelectContent>
                          {controllers.map((controller) => (
                            <SelectItem
                              key={controller.id}
                              value={controller.id.toString()}
                            >
                              {controller.lan_ip_address}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </CardContent>
                  </Card>
                ) : (
                  !loading.isLoading && (
                    <div className="text-center text-muted-foreground">
                      {getT(
                        "components.meters.no_controllers_found",
                        "No OpenDaylight controllers found."
                      )}
                    </div>
                  )
                )}

                {loading.isLoadingNodes || loading.isLoadingMeters ? (
                  <div className="flex justify-center items-center h-30vh">
                    <div className="space-y-4">
                      <Skeleton className="h-6 w-[150px]" />
                      <Skeleton className="h-4 w-[250px]" />
                    </div>
                  </div>
                ) : nodes.length > 0 ? (
                  <SwitchTabs
                    nodes={nodes}
                    meters={meters}
                    onOpenCategoriesDialog={handleOpenCategoriesDialog}
                    onOpenCreateDialog={handleOpenCreateDialog}
                    onDelete={handlePressDeleteMeter}
                  />
                ) : (
                  selectedController &&
                  !loading.isLoadingNodes && (
                    <div className="text-center text-muted-foreground">
                      {getT(
                        "components.meters.no_nodes_found",
                        "No nodes found for this controller."
                      )}
                    </div>
                  )
                )}
              </div>
            )}

            {/* Dialogs */}
            {selectedController && (
              <CreateMeterDialog
                open={dialog.isCreateDialogOpen}
                onClose={handleCloseCreateDialog}
                controllerIP={selectedController.lan_ip_address}
                switchNodeId={dialog.currentNodeOdlId}
                categories={categories}
                selectedModel={selectedModel}
              />
            )}

            {selectedController && dialog.currentMeter && (
              <ManageCategoriesDialog
                open={dialog.isCategoriesDialogOpen}
                onClose={handleCloseCategoriesDialog}
                categories={categories}
                meterCategories={
                  dialog.currentMeter.categories
                    ? dialog.currentMeter.categories.map((c) => c.name)
                    : []
                }
                meter={dialog.currentMeter}
                controllerIP={selectedController.lan_ip_address}
              />
            )}

            {selectedController && dialog.currentMeter && (
              <ConfirmDeleteMeterDialog
                open={dialog.isDeleteDialogOpen}
                onClose={handleCloseDeleteDialog}
                onConfirm={handleDeleteMeter}
                meter={dialog.currentMeter}
                controller={selectedController}
                switchNodeId={dialog.currentMeter.switch_node_id}
              />
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
