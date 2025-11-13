"use client";

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
import { useEffect, useState } from "react";
import { Controller } from "@/lib/types";

import ControllerItemComponent from "@/components/devices/ControllerItemComponent";
import InstallControllerDialog from "@/components/devices/InstallControllerDialog";
import DeleteControllerDialog from "@/components/devices/DeleteControllerDialog";
import { toast } from "sonner";
import { fetchControllers } from "@/lib/devices";
import { RingLoader } from "react-spinners";
import { PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function ControllersPage() {
  const { getT } = useLanguage();
  const [controllers, setControllers] = useState<Controller[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const [isInstallDialogOpen, setIsInstallDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [controllerToDelete, setControllerToDelete] =
    useState<Controller | null>(null);

  const router = useRouter();

  const fetchControllersData = async () => {
    setIsLoading(true);
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("taurineToken")
        : null;
    if (!token) {
      console.error("[CONTROLLERS PAGE] No token found");
      return;
    }
    try {
      const controllers = await fetchControllers(token);
      // console.log("[CONTROLLERS PAGE] controllers", controllers);
      setControllers(controllers);
      setIsLoading(false);
    } catch (error) {
      console.error("[CONTROLLERS PAGE] Error fetching controllers", error);
      toast.error("Error fetching controllers");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchControllersData();
  }, []);

  const handleInstallSuccess = async (message: string) => {
    await fetchControllersData();
    setIsInstallDialogOpen(false);
    toast.success(message);
  };

  const handleDeleteClick = (controller: Controller) => {
    setControllerToDelete(controller);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteSuccess = async () => {
    await fetchControllersData();
    setControllerToDelete(null);
    setIsDeleteDialogOpen(false);
    toast.success("Controller deleted successfully");
  };

  const handleDeleteClose = () => {
    setControllerToDelete(null);
    setIsDeleteDialogOpen(false);
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
                    <BreadcrumbLink href="/devices/controllers">
                      {getT("navigation.controllers", "Controllers")}
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
                  "page.ControllersPage.page_title",
                  "Manage your controllers"
                )}
              </h1>
              <div className="flex flex-col items-end gap-2">
                <Button
                  className="mt-1 bg-taurine-dark-purple hover:bg-taurine-dark-purple/80"
                  onClick={() => setIsInstallDialogOpen(true)}
                >
                  <PlusIcon className="w-4 h-4" />
                  {getT(
                    "page.ControllersPage.install_controller_button",
                    "Install Controller"
                  )}
                </Button>
              </div>
            </div>
            <div className="w-full flex items-center justify-center flex-col gap-4">
              {isLoading && (
                <div className="flex items-center justify-center w-full min-h-[400px]">
                  <RingLoader color="#7456FD" size={60} />
                </div>
              )}
              {!isLoading && (
                <div
                  className={`grid gap-4 w-full ${
                    controllers.length === 1
                      ? "grid-cols-1 max-w-[700px] mx-auto"
                      : "grid-cols-1 @xl/main:grid-cols-2"
                  }`}
                >
                  {controllers.map((controller) => (
                    <ControllerItemComponent
                      key={controller.id}
                      controller={controller}
                      onEdit={() => {
                        router.push(`/devices/controllers/${controller.id}`);
                      }}
                      onDelete={handleDeleteClick}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>

      <InstallControllerDialog
        isOpen={isInstallDialogOpen}
        onClose={() => setIsInstallDialogOpen(false)}
        onSuccess={handleInstallSuccess}
      />

      <DeleteControllerDialog
        controller={controllerToDelete}
        isOpen={isDeleteDialogOpen}
        onClose={handleDeleteClose}
        onSuccess={handleDeleteSuccess}
      />
    </ProtectedRoute>
  );
}
