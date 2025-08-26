/*
 * File: SwitchTabs.tsx
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OdlNode, OdlMeter, NetworkDeviceDetailResponse } from "@/lib/types";
import { fetchNetworkDevice } from "@/lib/networkDevice";
import { useLanguage } from "@/context/languageContext";

interface SwitchTabsProps {
  nodes: OdlNode[];
  meters: OdlMeter[];
  onOpenCategoriesDialog: (
    meter: OdlMeter,
    nodeOdlId: string,
    meterMacAddress: string
  ) => void;
  onOpenCreateDialog: (nodeOdlId: string) => void;
  onDelete: (meter: OdlMeter, nodeOdlId: string) => void;
}

export const SwitchTabs: React.FC<SwitchTabsProps> = ({
  nodes,
  meters,
  onOpenCategoriesDialog,
  onOpenCreateDialog,
  onDelete,
}) => {
  const { getT } = useLanguage();
  // Store device details by ID
  const [deviceDetails, setDeviceDetails] = useState<{
    [id: number]: NetworkDeviceDetailResponse;
  }>({});

  // Fetch device details for meters with a network_device ID
  useEffect(() => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;
    const idsToFetch = meters
      .map((m) => m.network_device)
      .filter(
        (id): id is number => typeof id === "number" && !(id in deviceDetails)
      );
    if (idsToFetch.length === 0) return;
    Promise.all(
      idsToFetch.map((id) =>
        fetchNetworkDevice(token, String(id)).then((details) => ({
          id,
          details,
        }))
      )
    ).then((results) => {
      setDeviceDetails((prev) => {
        const updated = { ...prev };
        for (const { id, details } of results) {
          updated[id] = details;
        }
        return updated;
      });
    });
  }, [meters, deviceDetails]);

  const getMetersForNode = (nodeOdlId: string): OdlMeter[] => {
    return meters.filter((meter) => meter.switch_node_id === nodeOdlId);
  };

  const formatActivationPeriod = (period: string): string => {
    switch (period) {
      case "all_week":
        return getT("components.meters.switch_tabs.all_week");
      case "weekday":
        return getT("components.meters.switch_tabs.weekday_only");
      case "weekend":
        return getT("components.meters.switch_tabs.weekend_only");
      default:
        return period;
    }
  };

  const formatTime = (time: string | null | undefined): string => {
    if (!time) return getT("components.meters.switch_tabs.not_available");
    return time;
  };

  return (
    <Tabs defaultValue={nodes[0]?.odl_node_id || ""} className="w-full">
      <TabsList className="grid w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
        {nodes.map((node) => (
          <TabsTrigger key={node.odl_node_id} value={node.odl_node_id}>
            {node.bridge_name || node.odl_node_id}
          </TabsTrigger>
        ))}
      </TabsList>

      {nodes.map((node) => {
        const nodeMeters = getMetersForNode(node.odl_node_id);

        return (
          <TabsContent
            key={node.odl_node_id}
            value={node.odl_node_id}
            className="space-y-4"
          >
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>
                      {node.bridge_name || node.odl_node_id}
                    </CardTitle>
                    <CardDescription>
                      Node ID: {node.odl_node_id} | Device: {node.device_name}
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => onOpenCreateDialog(node.odl_node_id)}
                    size="sm"
                  >
                    {getT("components.meters.switch_tabs.add_meter")}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {nodeMeters.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    {getT("components.meters.switch_tabs.no_meters")}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {nodeMeters.map((meter) => {
                      const device =
                        meter.network_device &&
                        deviceDetails[meter.network_device]
                          ? deviceDetails[meter.network_device]
                          : null;
                      console.log("[ SWITCH TABS ] device:", device);
                      return (
                        <Card
                          key={meter.id}
                          //   className="border-l-4 border-l-primary"
                        >
                          <CardContent className="pt-6">
                            <div className="flex items-start justify-between">
                              <div className="space-y-2 flex-1">
                                <div className="flex items-center gap-2">
                                  <h4 className="font-semibold">
                                    Meter {meter.meter_id_on_odl}
                                  </h4>
                                  <Badge variant="outline">
                                    {meter.rate} Kbps
                                  </Badge>
                                  <Badge variant="secondary">
                                    {formatActivationPeriod(
                                      meter.activation_period
                                    )}
                                  </Badge>
                                </div>

                                {meter.categories.length > 0 && (
                                  <div className="flex flex-wrap gap-1">
                                    {meter.categories.map((category) => (
                                      <Badge
                                        key={category.name}
                                        variant="default"
                                      >
                                        {category.name}
                                      </Badge>
                                    ))}
                                  </div>
                                )}

                                <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                                  {(meter.start_time || meter.end_time) && (
                                    <>
                                      <div>
                                        <strong>
                                          {getT(
                                            "components.meters.switch_tabs.start_time"
                                          )}
                                          :
                                        </strong>{" "}
                                        {formatTime(meter.start_time)}
                                      </div>
                                      <div>
                                        <strong>
                                          {getT(
                                            "components.meters.switch_tabs.end_time"
                                          )}
                                          :
                                        </strong>{" "}
                                        {formatTime(meter.end_time)}
                                      </div>
                                    </>
                                  )}

                                  {device && (
                                    <div className="col-span-2">
                                      <strong>
                                        {getT(
                                          "components.meters.switch_tabs.device"
                                        )}
                                        :
                                      </strong>{" "}
                                      {device.name
                                        ? device.name
                                        : getT(
                                            "components.meters.switch_tabs.no_name"
                                          )}
                                      {"@"}
                                      {device.ip_address}
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="flex gap-2 ml-4">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() =>
                                    onOpenCategoriesDialog(
                                      meter,
                                      node.odl_node_id,
                                      meter.network_device_mac || ""
                                    )
                                  }
                                >
                                  {getT(
                                    "components.meters.switch_tabs.manage_categories"
                                  )}
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() =>
                                    onDelete(meter, node.odl_node_id)
                                  }
                                >
                                  {getT("components.meters.switch_tabs.delete")}
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        );
      })}
    </Tabs>
  );
};
