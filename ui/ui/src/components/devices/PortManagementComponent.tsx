"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { Loader2Icon } from "lucide-react";
import {
  fetchBridgePorts,
  updatePortLinkSpeed,
  syncPortDetails,
} from "@/lib/devices";
import { BridgePort, BridgePortsResponse } from "@/lib/types";
import { useLanguage } from "@/context/languageContext";

export interface PortManagementComponentProps {
  switchId: string;
  fetchData?: () => Promise<void>;
  isLoading: boolean;
}

const PortManagementComponent: React.FC<PortManagementComponentProps> = ({
  switchId,
  fetchData,
  isLoading: parentLoading,
}) => {
  const { getT } = useLanguage();
  const [ports, setPorts] = useState<BridgePort[]>([]);
  const [isLoadingPorts, setIsLoadingPorts] = useState(true);
  const [editingPortId, setEditingPortId] = useState<number | null>(null);
  const [editingLinkSpeed, setEditingLinkSpeed] = useState<string>("");
  const [syncingPortIds, setSyncingPortIds] = useState<Set<number>>(new Set());
  const [savingPortIds, setSavingPortIds] = useState<Set<number>>(new Set());

  const loadPorts = useCallback(async () => {
    setIsLoadingPorts(true);
    try {
      const token = localStorage.getItem("taurineToken") || "";
      const data: BridgePortsResponse = await fetchBridgePorts(token, switchId);
      setPorts(data.ports || []);
    } catch (error) {
      console.error("Error fetching ports:", error);
      toast.error(getT("components.devices.port_management.error_fetching"));
      setPorts([]);
    } finally {
      setIsLoadingPorts(false);
    }
  }, [switchId, getT]);

  useEffect(() => {
    loadPorts();
  }, [loadPorts]);

  const formatLinkSpeed = (speed: number | null): string => {
    if (speed === null) return "N/A";
    if (speed >= 10000) {
      return `${speed / 1000} Gb/s`;
    }
    return `${speed} Mb/s`;
  };

  const getStatusBadge = (isUp: boolean | null) => {
    if (isUp === true) {
      return (
        <Badge className="bg-green-500 hover:bg-green-600">
          {getT("components.devices.port_management.status_up")}
        </Badge>
      );
    }
    if (isUp === false) {
      return (
        <Badge className="bg-red-500 hover:bg-red-600">
          {getT("components.devices.port_management.status_down")}
        </Badge>
      );
    }
    return (
      <Badge variant="secondary">
        {getT("components.devices.port_management.status_unknown")}
      </Badge>
    );
  };

  const handleEditClick = (port: BridgePort) => {
    setEditingPortId(port.id);
    setEditingLinkSpeed(port.link_speed?.toString() || "");
  };

  const handleCancelEdit = () => {
    setEditingPortId(null);
    setEditingLinkSpeed("");
  };

  const handleSaveLinkSpeed = async (portId: number) => {
    const linkSpeedValue = parseInt(editingLinkSpeed, 10);

    if (
      isNaN(linkSpeedValue) ||
      linkSpeedValue < 10 ||
      linkSpeedValue > 100000
    ) {
      toast.error(
        getT("components.devices.port_management.link_speed_invalid")
      );
      return;
    }

    setSavingPortIds((prev) => new Set(prev).add(portId));
    try {
      const token = localStorage.getItem("taurineToken") || "";
      const updatedPort = await updatePortLinkSpeed(
        token,
        portId,
        linkSpeedValue
      );

      setPorts((prevPorts) =>
        prevPorts.map((p) => (p.id === portId ? updatedPort : p))
      );
      setEditingPortId(null);
      setEditingLinkSpeed("");
      toast.success(getT("components.devices.port_management.update_success"));
      if (fetchData) await fetchData();
    } catch (error) {
      console.error("Error updating port:", error);
      toast.error(getT("components.devices.port_management.update_error"));
    } finally {
      setSavingPortIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(portId);
        return newSet;
      });
    }
  };

  const handleSyncPort = async (portId: number) => {
    setSyncingPortIds((prev) => new Set(prev).add(portId));
    try {
      const token = localStorage.getItem("taurineToken") || "";
      const updatedPort = await syncPortDetails(token, portId);

      setPorts((prevPorts) =>
        prevPorts.map((p) => (p.id === portId ? updatedPort : p))
      );
      toast.success(getT("components.devices.port_management.sync_success"));
    } catch (error) {
      console.error("Error syncing port:", error);
      const errorMessage =
        error instanceof Error && "response" in error
          ? (error as { response?: { data?: { error?: string } } }).response
              ?.data?.error ||
            getT("components.devices.port_management.sync_error")
          : getT("components.devices.port_management.sync_error");
      toast.error(errorMessage);
    } finally {
      setSyncingPortIds((prev) => {
        const newSet = new Set(prev);
        newSet.delete(portId);
        return newSet;
      });
    }
  };

  if (parentLoading || isLoadingPorts) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>
            {getT("components.devices.port_management.title")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-2">
            <Skeleton className="h-10 w-full bg-muted" />
            <Skeleton className="h-10 w-full bg-muted" />
            <Skeleton className="h-10 w-full bg-muted" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (ports.length === 0) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>
            {getT("components.devices.port_management.title")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground text-center py-8">
            {getT("components.devices.port_management.no_ports")}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>
          {getT("components.devices.port_management.title")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  {getT("components.devices.port_management.port_name")}
                </TableHead>
                <TableHead>
                  {getT("components.devices.port_management.ovs_port_number")}
                </TableHead>
                <TableHead>
                  {getT("components.devices.port_management.link_speed")}
                </TableHead>
                <TableHead>
                  {getT("components.devices.port_management.status")}
                </TableHead>
                <TableHead className="text-right">
                  {getT("components.devices.port_management.actions")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ports.map((port) => (
                <TableRow key={port.id}>
                  <TableCell className="font-medium">{port.name}</TableCell>
                  <TableCell>
                    {port.ovs_port_number !== null
                      ? port.ovs_port_number
                      : "N/A"}
                  </TableCell>
                  <TableCell>
                    {editingPortId === port.id ? (
                      <div className="flex items-center gap-2">
                        <Input
                          type="number"
                          value={editingLinkSpeed}
                          onChange={(e) => setEditingLinkSpeed(e.target.value)}
                          placeholder={getT(
                            "components.devices.port_management.link_speed_placeholder"
                          )}
                          className="w-32"
                          disabled={savingPortIds.has(port.id)}
                          min={10}
                          max={100000}
                        />
                        <Button
                          size="sm"
                          onClick={() => handleSaveLinkSpeed(port.id)}
                          disabled={savingPortIds.has(port.id)}
                        >
                          {savingPortIds.has(port.id) ? (
                            <Loader2Icon className="animate-spin w-4 h-4" />
                          ) : (
                            getT("components.devices.port_management.save")
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={handleCancelEdit}
                          disabled={savingPortIds.has(port.id)}
                        >
                          {getT("components.devices.port_management.cancel")}
                        </Button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <span>{formatLinkSpeed(port.link_speed)}</span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditClick(port)}
                          disabled={
                            syncingPortIds.has(port.id) ||
                            savingPortIds.has(port.id)
                          }
                        >
                          {getT(
                            "components.devices.port_management.edit_speed"
                          )}
                        </Button>
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{getStatusBadge(port.is_up)}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSyncPort(port.id)}
                      disabled={
                        syncingPortIds.has(port.id) ||
                        savingPortIds.has(port.id) ||
                        editingPortId === port.id
                      }
                    >
                      {syncingPortIds.has(port.id) ? (
                        <>
                          <Loader2Icon className="animate-spin w-4 h-4 mr-2" />
                          {getT("components.devices.port_management.syncing")}
                        </>
                      ) : (
                        getT("components.devices.port_management.sync")
                      )}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

export default PortManagementComponent;
