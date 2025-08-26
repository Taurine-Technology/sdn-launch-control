/*
 * File: DeleteBridgeDialog.tsx
 * Copyright (C) 2025 Keegan White
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Keegan White exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

import React from "react";
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
import { RingLoader } from "react-spinners";
import { useLanguage } from "@/context/languageContext";

interface DeleteBridgeDialogProps {
  onClose: () => void;
  bridgeName: string;
  handleDelete: () => Promise<void>;
  isOpen: boolean;
  isDeleting: boolean;
}

const DeleteBridgeDialog: React.FC<DeleteBridgeDialogProps> = ({
  bridgeName,
  handleDelete,
  onClose,
  isOpen,
  isDeleting,
}) => {
  const { getT } = useLanguage();
  const handleClose = () => {
    onClose();
  };

  return (
    <AlertDialog open={isOpen}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>
            {getT("components.devices.delete_bridge_dialog.title")}
          </AlertDialogTitle>
          {isDeleting ? (
            <div className="flex flex-col items-center gap-3">
              <RingLoader color="#7456FD" size={60} />
            </div>
          ) : (
            <AlertDialogDescription>
              {getT(
                "components.devices.delete_bridge_dialog.description",
                `Are you sure you want to delete the bridge "${bridgeName}"? This action cannot be undone and will remove the bridge from the device.`
              )}
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting} onClick={handleClose}>
            {getT("components.devices.delete_bridge_dialog.cancel")}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            disabled={isDeleting}
          >
            {isDeleting
              ? getT("components.devices.delete_bridge_dialog.deleting")
              : getT("components.devices.delete_bridge_dialog.delete")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default DeleteBridgeDialog;
