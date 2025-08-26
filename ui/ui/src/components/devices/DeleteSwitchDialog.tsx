"use client";
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
import { Loader2, Trash2 } from "lucide-react";
import { useLanguage } from "@/context/languageContext";

interface DeleteSwitchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
  switchName?: string;
}

export default function DeleteSwitchDialog({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
  switchName,
}: DeleteSwitchDialogProps) {
  const { getT } = useLanguage();

  return (
    <AlertDialog
      open={isOpen}
      onOpenChange={(open) => {
        // Only allow closing if not loading
        if (!open && !isLoading) {
          onClose();
        }
      }}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-destructive" />
            {getT("page.SwitchesPage.delete_dialog_title", "Delete Switch")}
          </AlertDialogTitle>
          <AlertDialogDescription>
            {getT(
              "page.SwitchesPage.delete_dialog_description",
              `Are you sure you want to delete ${
                switchName || "this switch"
              }? This action will remove the switch from the system and clean up associated bridges and controllers. This action cannot be undone.`
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isLoading}>
            {getT("common.cancel", "Cancel")}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isLoading}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {getT("common.deleting", "Deleting...")}
              </>
            ) : (
              getT("common.delete", "Delete")
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
