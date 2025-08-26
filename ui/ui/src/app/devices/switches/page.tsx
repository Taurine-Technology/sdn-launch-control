"use client";
import { useEffect, useState } from "react";
import { fetchSwitches, deleteSwitch, forceDeleteSwitch } from "@/lib/devices";
import { NetworkDeviceDetails } from "@/lib/types";
import { Button } from "@/components/ui/button";
import SwitchItemComponent from "@/components/devices/SwitchItemComponent";
import DeleteSwitchDialog from "@/components/devices/DeleteSwitchDialog";
import NukeSwitchDialog from "@/components/devices/NukeSwitchDialog";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { useLanguage } from "@/context/languageContext";
import ProtectedRoute from "@/lib/ProtectedRoute";
import InstallOvsDialog from "@/components/devices/InstallOvsDialog";
import { installOvs } from "@/lib/devices";
import { PlusIcon } from "lucide-react";
import { RingLoader } from "react-spinners";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { Skeleton } from "@/components/ui/skeleton";

export default function SwitchesPage() {
  const { getT } = useLanguage();
  const [switches, setSwitches] = useState<NetworkDeviceDetails[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [installDialogOpen, setInstallDialogOpen] = useState(false);
  const [installingOvs, setInstallingOvs] = useState(false);
  const [installResponse, setInstallResponse] = useState<string>("");
  const [installResponseType, setInstallResponseType] = useState<
    "success" | "error" | undefined
  >(undefined);

  // Delete and nuke dialog states
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [nukeDialogOpen, setNukeDialogOpen] = useState(false);
  const [switchToDelete, setSwitchToDelete] =
    useState<NetworkDeviceDetails | null>(null);
  const [switchToNuke, setSwitchToNuke] = useState<NetworkDeviceDetails | null>(
    null
  );
  const [isDeleting, setIsDeleting] = useState(false);

  const router = useRouter();

  const getSwitches = async () => {
    setIsLoading(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken")
          : null;
      if (!token) throw new Error("No auth token found");
      const data = await fetchSwitches(token);
      const results = Array.isArray(data) ? data : data.results;
      setSwitches(results.filter((d) => d.device_type === "switch"));
    } catch (err: unknown) {
      console.error("Failed to fetch switches:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    getSwitches();
  }, []);

  const handleOpenInstallDialog = () => {
    setInstallDialogOpen(true);
    setInstallResponse("");
    setInstallResponseType(undefined);
  };

  const handleCloseInstallDialog = () => {
    setInstallDialogOpen(false);
    setInstallResponse("");
    setInstallResponseType(undefined);
  };

  const handleInstallOvs = async (payload: Record<string, unknown>) => {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("taurineToken")
        : null;
    if (!token) return;
    setInstallingOvs(true);
    setInstallResponse("");
    setInstallResponseType(undefined);
    try {
      const response = await installOvs(token, payload);
      setInstallResponse(response?.message || "Success");
      setInstallResponseType("success");
      await getSwitches();
      toast.success(
        getT(
          "page.SwitchesPage.install_success_toast",
          "Device installed successfully!"
        ),
        {
          richColors: true,
        }
      );
      setInstallDialogOpen(false);
    } catch (error: unknown) {
      const errorMessage =
        error &&
        typeof error === "object" &&
        "response" in error &&
        error.response &&
        typeof error.response === "object" &&
        "data" in error.response &&
        error.response.data &&
        typeof error.response.data === "object" &&
        "message" in error.response.data
          ? String(error.response.data.message)
          : getT(
              "page.SwitchesPage.failed_to_install_ovs",
              "Failed to install OVS."
            );

      setInstallResponse(errorMessage);
      toast.error(`Error installing OVS: ${errorMessage}`, {
        richColors: true,
      });
      setInstallResponseType("error");
    } finally {
      setInstallingOvs(false);
    }
  };

  // Delete switch handlers
  const handleDeleteClick = (device: NetworkDeviceDetails) => {
    setSwitchToDelete(device);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!switchToDelete || !switchToDelete.lan_ip_address) return;

    setIsDeleting(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken")
          : null;
      if (!token) throw new Error("No auth token found");

      const payload = { lan_ip_address: switchToDelete.lan_ip_address };
      const response = await deleteSwitch(token, payload);

      if (response.status === "success") {
        toast.success(
          getT(
            "page.SwitchesPage.delete_success_toast",
            "Switch deleted successfully!"
          ),
          { richColors: true }
        );
        await getSwitches(); // Refresh the list
      } else {
        toast.error(
          response.message ||
            getT(
              "page.SwitchesPage.delete_error_toast",
              "Failed to delete switch"
            ),
          { richColors: true }
        );
      }
    } catch (error: unknown) {
      const errorMessage =
        error &&
        typeof error === "object" &&
        "response" in error &&
        error.response &&
        typeof error.response === "object" &&
        "data" in error.response &&
        error.response.data &&
        typeof error.response.data === "object" &&
        "message" in error.response.data
          ? String(error.response.data.message)
          : getT(
              "page.SwitchesPage.delete_error_toast",
              "Failed to delete switch"
            );

      toast.error(`Error deleting switch: ${errorMessage}`, {
        richColors: true,
      });
    } finally {
      setIsDeleting(false);
      setDeleteDialogOpen(false);
      setSwitchToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setSwitchToDelete(null);
  };

  // Nuke switch handlers
  const handleNukeClick = (device: NetworkDeviceDetails) => {
    setSwitchToNuke(device);
    setNukeDialogOpen(true);
  };

  const handleNukeConfirm = async () => {
    if (!switchToNuke || !switchToNuke.lan_ip_address) return;

    setIsDeleting(true);
    try {
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("taurineToken")
          : null;
      if (!token) throw new Error("No auth token found");

      const payload = { lan_ip_address: switchToNuke.lan_ip_address };
      const response = await forceDeleteSwitch(token, payload);

      if (response.status === "success") {
        toast.success(
          getT(
            "page.SwitchesPage.nuke_success_toast",
            "Switch force deleted successfully!"
          ),
          { richColors: true }
        );
        await getSwitches(); // Refresh the list
      } else {
        toast.error(
          response.message ||
            getT(
              "page.SwitchesPage.nuke_error_toast",
              "Failed to force delete switch"
            ),
          { richColors: true }
        );
      }
    } catch (error: unknown) {
      const errorMessage =
        error &&
        typeof error === "object" &&
        "response" in error &&
        error.response &&
        typeof error.response === "object" &&
        "data" in error.response &&
        error.response.data &&
        typeof error.response.data === "object" &&
        "message" in error.response.data
          ? String(error.response.data.message)
          : getT(
              "page.SwitchesPage.nuke_error_toast",
              "Failed to force delete switch"
            );

      toast.error(`Error force deleting switch: ${errorMessage}`, {
        richColors: true,
      });
    } finally {
      setIsDeleting(false);
      setNukeDialogOpen(false);
      setSwitchToNuke(null);
    }
  };

  const handleNukeCancel = () => {
    setNukeDialogOpen(false);
    setSwitchToNuke(null);
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
                    <BreadcrumbLink href="/dashboard">
                      {getT("navigation.dashboard", "Dashboard")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator className="hidden md:block" />
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/devices/switches">
                      {getT("navigation.switches", "Switches")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>
          <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
            <div className="w-full flex flex-row items-end justify-between mb-6">
              <h1 className="text-2xl font-bold text-muted-foreground">
                {getT("page.SwitchesPage.page_title", "Manage your switches")}
              </h1>

              <div className="flex flex-col items-end gap-2">
                <Button
                  className="mt-1 bg-taurine-dark-purple hover:bg-taurine-dark-purple/80"
                  onClick={handleOpenInstallDialog}
                >
                  <PlusIcon className="w-4 h-4" />
                  {getT("page.SwitchesPage.install_ovs_button", "Add Switch")}
                </Button>
              </div>
            </div>
            <div className="w-full flex items-center justify-center flex-col gap-4">
              <div className="relative grid grid-cols-1 @xl/main:grid-cols-2 gap-4 w-full">
                {isLoading ? (
                  <>
                    {/* Skeleton Cards */}
                    <Skeleton className="h-[200px] w-full bg-muted-foreground/30" />
                    <Skeleton className="h-[200px] w-full bg-muted-foreground/30" />

                    {/* Centered RingLoader overlay */}
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50">
                      <RingLoader color="#7456FD" size={60} />
                    </div>
                  </>
                ) : (
                  <>
                    {switches.map((sw) => (
                      <SwitchItemComponent
                        key={sw.id}
                        device={sw}
                        onView={(id) => router.push(`/devices/switches/${id}`)}
                        onDelete={handleDeleteClick}
                        onNuke={handleNukeClick}
                      />
                    ))}
                  </>
                )}
              </div>
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
      <InstallOvsDialog
        isOpen={installDialogOpen}
        onClose={handleCloseInstallDialog}
        onInstall={handleInstallOvs}
        switches={switches}
        isLoading={installingOvs}
        response={installResponse}
        responseType={installResponseType}
        disableClose={installingOvs}
      />

      {/* Delete Switch Dialog */}
      <DeleteSwitchDialog
        isOpen={deleteDialogOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        isLoading={isDeleting}
        switchName={switchToDelete?.name}
      />

      {/* Nuke Switch Dialog */}
      <NukeSwitchDialog
        isOpen={nukeDialogOpen}
        onClose={handleNukeCancel}
        onConfirm={handleNukeConfirm}
        isLoading={isDeleting}
        switchName={switchToNuke?.name}
      />
    </ProtectedRoute>
  );
}
