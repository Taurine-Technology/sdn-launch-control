/*
 * File: ConfirmDeleteMeterDialog.tsx
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

"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/context/languageContext";

import { OdlController, OdlMeter } from "@/lib/types";

interface ConfirmDeleteMeterDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  meter: OdlMeter;
  controller: OdlController;
  switchNodeId: string;
}

export const ConfirmDeleteMeterDialog: React.FC<
  ConfirmDeleteMeterDialogProps
> = ({ open, onClose, onConfirm, meter, controller, switchNodeId }) => {
  const { getT } = useLanguage();
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {getT("components.meters.confirm_delete_meter_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.meters.confirm_delete_meter_dialog.description")}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <div className="text-sm">
              <strong>
                {getT("components.meters.confirm_delete_meter_dialog.meter_id")}
                :
              </strong>{" "}
              {meter.meter_id_on_odl}
            </div>
            <div className="text-sm">
              <strong>
                {getT("components.meters.confirm_delete_meter_dialog.rate")}:
              </strong>{" "}
              {meter.rate} Kbps
            </div>
            <div className="text-sm">
              <strong>
                {getT("components.meters.confirm_delete_meter_dialog.switch")}:
              </strong>{" "}
              {switchNodeId}
            </div>
            <div className="text-sm">
              <strong>
                {getT(
                  "components.meters.confirm_delete_meter_dialog.controller"
                )}
                :
              </strong>{" "}
              {controller.lan_ip_address}
            </div>
            {meter.categories.length > 0 && (
              <div className="text-sm">
                <strong>
                  {getT(
                    "components.meters.confirm_delete_meter_dialog.categories"
                  )}
                  :
                </strong>{" "}
                {meter.categories.map((c) => c.name).join(", ")}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {getT("components.meters.confirm_delete_meter_dialog.cancel")}
          </Button>
          <Button variant="destructive" onClick={onConfirm}>
            {getT("components.meters.confirm_delete_meter_dialog.delete")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
