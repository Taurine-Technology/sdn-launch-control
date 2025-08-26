"use client";

import { useState } from "react";
import { Controller } from "@/lib/types";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import { Loader2Icon } from "lucide-react";
import { deleteController } from "@/lib/devices";
import { toast } from "sonner";

interface DeleteControllerDialogProps {
  controller: Controller | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function DeleteControllerDialog({
  controller,
  isOpen,
  onClose,
  onSuccess,
}: DeleteControllerDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!controller) return;

    setIsDeleting(true);
    try {
      const token = localStorage.getItem("taurineToken");
      if (!token) {
        throw new Error("No authentication token found");
      }

      const response = await deleteController(token, {
        lan_ip_address: controller.lan_ip_address || "",
      });

      console.log(
        "[DELETECONTROLLERDIALOG.tsx] deleteController response",
        response
      );

      if (
        response.status === "success" ||
        (response.status === "error" && !response.message)
      ) {
        // Django returns 204 No Content on success, so we consider it successful

        onSuccess();
      } else {
        throw new Error(response.message || "Failed to delete controller");
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete controller";
      toast.error(errorMessage);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClose = () => {
    if (!isDeleting) {
      onClose();
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={handleClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Controller</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the controller at{" "}
            <span className="font-mono text-foreground">
              {controller?.lan_ip_address}
            </span>
            ? This action cannot be undone and will remove all associated
            bridges and configurations.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? (
              <>
                <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                Deleting...
              </>
            ) : (
              "Delete Controller"
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
