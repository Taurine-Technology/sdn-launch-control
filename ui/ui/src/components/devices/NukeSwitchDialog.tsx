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
import { Loader2, Bomb } from "lucide-react";
import { useLanguage } from "@/context/languageContext";

interface NukeSwitchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
  switchName?: string;
}

export default function NukeSwitchDialog({
  isOpen,
  onClose,
  onConfirm,
  isLoading,
  switchName,
}: NukeSwitchDialogProps) {
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
          <AlertDialogTitle className="flex items-center gap-2 text-destructive">
            <Bomb className="w-5 h-5" />
            {getT(
              "page.SwitchesPage.nuke_dialog_title",
              "WARNING - Force Delete"
            )}
          </AlertDialogTitle>
          <AlertDialogDescription className="text-destructive">
            {getT(
              "page.SwitchesPage.nuke_dialog_description",
              `Are you absolutely sure you want to force delete ${
                switchName || "this switch"
              }? This action is permanent and will only remove the device from Launch Control's database without changing any device settings. This action cannot be undone.`
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
                {getT("common.nuking", "Force Deleting...")}
              </>
            ) : (
              getT("common.nuke", "Force Delete")
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
