/*
 * File: ManageCategoriesDialog.tsx
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

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { odlUpdateMeter } from "@/lib/odl";
import { OdlMeter, UpdateOdlMeterRequest } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";
import { useModel } from "@/context/ModelContext";

interface ManageCategoriesDialogProps {
  open: boolean;
  onClose: (success: boolean) => void;
  categories: string[];
  meterCategories: string[];
  meter: OdlMeter;
  controllerIP: string;
}

export const ManageCategoriesDialog: React.FC<ManageCategoriesDialogProps> = ({
  open,
  onClose,
  categories,
  meterCategories,
  meter,
  controllerIP,
}) => {
  const { getT } = useLanguage();
  const { activeModel } = useModel();
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (open && meterCategories) {
      setSelectedCategories(meterCategories);
      console.log("[ CATEGORY UPDATE ] Current meter on open:", meter);
    } else if (!open) {
      setSelectedCategories([]);
    }
  }, [open, meterCategories, meter]);

  const handleCloseDialog = () => {
    if (!isLoading) {
      onClose(false);
    }
  };

  const handleSubmit = async () => {
    if (!meter || !meter.id) {
      toast.error(
        getT("components.meters.manage_categories_dialog.meter_missing")
      );
      return;
    }

    setIsLoading(true);

    const token = localStorage.getItem("taurineToken");
    if (!token) {
      toast.error(
        getT("components.meters.manage_categories_dialog.auth_token_not_found")
      );
      setIsLoading(false);
      return;
    }

    const payload: UpdateOdlMeterRequest = {
      controller_ip: controllerIP,
      switch_id: meter.switch_node_id,
      meter_id: parseInt(meter.meter_id_on_odl, 10),
      rate: parseInt(meter.rate.toString(), 10),
      categories: selectedCategories,
      model_name: activeModel?.name || "",
      mac_address: meter.network_device_mac || null,
      activation_period: meter.activation_period,
      start_time: meter.start_time || null,
      end_time: meter.end_time || null,
    };

    console.log("[ CATEGORY UPDATE ] payload obj:", payload);

    try {
      await odlUpdateMeter(token, meter.id, payload);
      toast.success(getT("components.meters.manage_categories_dialog.success"));
      onClose(true);
    } catch (error: unknown) {
      const errMsg =
        error instanceof Error
          ? error.message
          : getT("components.meters.manage_categories_dialog.error");
      toast.error(errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryChange = (category: string, checked: boolean) => {
    if (checked) {
      setSelectedCategories((prev) => [...prev, category]);
    } else {
      setSelectedCategories((prev) => prev.filter((c) => c !== category));
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleCloseDialog}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {getT("components.meters.manage_categories_dialog.title")}
          </DialogTitle>
          <DialogDescription>
            {getT("components.meters.manage_categories_dialog.description")}
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* Model Information */}
          {activeModel && (
            <div className="grid gap-2">
              <label className="text-sm font-medium">
                {getT(
                  "components.meters.manage_categories_dialog.model_info",
                  "Model Information"
                )}
              </label>
              <div className="flex items-center gap-2 p-3 bg-muted rounded-md">
                <Badge variant="outline" className="text-sm">
                  {getT(
                    "components.meters.manage_categories_dialog.active_model",
                    "Active Model"
                  )}
                  :
                </Badge>
                <span className="text-sm font-medium">{activeModel.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({activeModel.num_categories} categories)
                </span>
              </div>
            </div>
          )}

          <div className="grid gap-2">
            <label className="text-sm font-medium">
              {getT("components.meters.manage_categories_dialog.categories")}
            </label>
            <ScrollArea className="h-[200px] w-full rounded-md border p-4">
              <div className="grid grid-cols-2 gap-2">
                {categories.map((category) => (
                  <div key={category} className="flex items-center space-x-2">
                    <Checkbox
                      id={category}
                      checked={selectedCategories.includes(category)}
                      onCheckedChange={(checked) =>
                        handleCategoryChange(category, checked as boolean)
                      }
                    />
                    <label htmlFor={category} className="text-sm">
                      {category}
                    </label>
                  </div>
                ))}
              </div>
            </ScrollArea>
            {selectedCategories.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {selectedCategories.map((category) => (
                  <Badge key={category} variant="secondary">
                    {category}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleCloseDialog}
            disabled={isLoading}
          >
            {getT("components.meters.manage_categories_dialog.cancel")}
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading}>
            {isLoading
              ? getT("components.meters.manage_categories_dialog.saving")
              : getT("components.meters.manage_categories_dialog.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
