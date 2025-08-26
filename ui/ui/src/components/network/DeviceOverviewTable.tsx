"use client";
import React from "react";
import { NetworkDeviceDetails } from "@/lib/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { RingLoader } from "react-spinners";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import { Skeleton } from "@/components/ui/skeleton";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { PencilIcon } from "lucide-react";
import { EditDeviceDialog } from "./EditDeviceDialog";
import { useState } from "react";
import { updateNetworkDevice } from "@/lib/devices";
import { toast } from "sonner";
import { useLanguage } from "@/context/languageContext";

interface DeviceOverviewTableProps {
  devices: NetworkDeviceDetails[];
  count: number;
  isLoading: boolean;
  error: string;
  search: string;
  setSearch: (v: string) => void;
  filterType: string;
  setFilterType: (v: string) => void;
  filterVerified: string;
  setFilterVerified: (v: string) => void;
  page: number;
  setPage: (v: number) => void;
  pageSize: number;
  setPageSize: (v: number) => void;
  deviceTypeOptions: { value: string; label: string }[];
  verifiedOptions: { value: string; label: string }[];
  onDeviceUpdated?: () => void;
}

export const DeviceOverviewTable: React.FC<DeviceOverviewTableProps> = ({
  devices,
  count,
  isLoading,
  error,
  search,
  setSearch,
  filterType,
  setFilterType,
  filterVerified,
  setFilterVerified,
  page,
  setPage,
  pageSize,
  setPageSize,
  deviceTypeOptions,
  verifiedOptions,
  onDeviceUpdated,
}) => {
  const { getT } = useLanguage();
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] =
    useState<NetworkDeviceDetails | null>(null);
  const [editLoading, setEditLoading] = useState(false);

  const handleEditDevice = (device: NetworkDeviceDetails) => {
    setSelectedDevice(device);
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setSelectedDevice(null);
  };

  const handleSaveDevice = async (
    deviceId: string,
    updatedData: Partial<NetworkDeviceDetails>
  ) => {
    setEditLoading(true);
    try {
      const token = localStorage.getItem("taurineToken") || "";
      await updateNetworkDevice(token, deviceId, updatedData);

      handleCloseEditDialog();
      // Trigger a refresh of the devices list
      toast.success(
        getT("components.network.device_overview_table.device_updated_success")
      );
      onDeviceUpdated?.();
    } catch (error) {
      console.error("Failed to update device:", error);
      toast.error(
        getT("components.network.device_overview_table.device_update_error")
      );
      throw error; // Re-throw to keep dialog open
    } finally {
      setEditLoading(false);
    }
  };
  return (
    <ProtectedRoute>
      <div className="w-full p-6">
        {/* Top controls: search left, filters right */}
        <div className="flex flex-wrap items-center justify-between mb-4 gap-2">
          <Input
            placeholder={getT(
              "components.network.device_overview_table.search_placeholder"
            )}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="max-w-xs"
          />
          <div className="flex gap-2">
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-40">
                <SelectValue
                  placeholder={getT(
                    "components.network.device_overview_table.device_type_placeholder"
                  )}
                />
              </SelectTrigger>
              <SelectContent>
                {deviceTypeOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterVerified} onValueChange={setFilterVerified}>
              <SelectTrigger className="w-32">
                <SelectValue
                  placeholder={getT(
                    "components.network.device_overview_table.verified_placeholder"
                  )}
                />
              </SelectTrigger>
              <SelectContent>
                {verifiedOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {error && <div className="text-destructive mb-2">{error}</div>}
        {isLoading ? (
          <div className="relative w-full">
            {/* Skeleton Card */}
            <div className="flex flex-col space-y-3 w-full">
              <Skeleton className="h-[320px] w-full bg-card" />
            </div>
            {/* Spinner overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <RingLoader color="#7456FD" size={40} />
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader className="bg-card">
                <TableRow>
                  <TableHead>
                    {getT(
                      "components.network.device_overview_table.mac_address"
                    )}
                  </TableHead>
                  <TableHead>
                    {getT("components.network.device_overview_table.name")}
                  </TableHead>
                  <TableHead>
                    {getT(
                      "components.network.device_overview_table.device_type"
                    )}
                  </TableHead>
                  <TableHead>
                    {getT(
                      "components.network.device_overview_table.operating_system"
                    )}
                  </TableHead>
                  <TableHead>
                    {getT(
                      "components.network.device_overview_table.ip_address"
                    )}
                  </TableHead>
                  <TableHead>
                    {getT("components.network.device_overview_table.verified")}
                  </TableHead>
                  <TableHead>
                    {getT("components.network.device_overview_table.actions")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {devices.length ? (
                  devices.map((device) => (
                    <TableRow key={device.id}>
                      <TableCell>{device.mac_address}</TableCell>
                      <TableCell>{device.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="px-2">
                          {device.device_type === "end_user"
                            ? "End User"
                            : device.device_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {device.operating_system === "ubuntu_22_server"
                          ? "Ubuntu Server 22"
                          : device.operating_system}
                      </TableCell>
                      <TableCell>{device.ip_address}</TableCell>
                      <TableCell>
                        {device.verified ? (
                          <Badge variant="default" className="bg-green-600">
                            {getT(
                              "components.network.device_overview_table.verified_badge"
                            )}
                          </Badge>
                        ) : (
                          <Badge
                            variant="outline"
                            className="bg-destructive/10 text-destructive"
                          >
                            {getT(
                              "components.network.device_overview_table.not_verified_badge"
                            )}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditDevice(device)}
                          className="h-8 w-8 p-0"
                        >
                          <PencilIcon className="h-4 w-4" />
                          <span className="sr-only">
                            {getT(
                              "components.network.device_overview_table.edit_device"
                            )}
                          </span>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center">
                      {getT(
                        "components.network.device_overview_table.no_results"
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        )}
        {/* Pagination Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-center mt-4 gap-2">
          <span className="text-sm text-muted-foreground">
            {getT("components.network.device_overview_table.total_devices")}{" "}
            {count}
          </span>
          <div className="flex items-center gap-4 flex-nowrap">
            <div className="flex items-center gap-2 flex-nowrap">
              <span className="text-sm text-muted-foreground">
                {getT("components.network.device_overview_table.rows")}
              </span>
              <Select
                value={String(pageSize)}
                onValueChange={(v: string) => setPageSize(Number(v))}
              >
                <SelectTrigger className="w-20">
                  <SelectValue placeholder={String(pageSize)} />
                </SelectTrigger>
                <SelectContent>
                  {[5, 10, 20, 50, 100].map((size) => (
                    <SelectItem key={size} value={String(size)}>
                      {size}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      if (page > 1) setPage(page - 1);
                    }}
                    aria-disabled={page === 1}
                  />
                </PaginationItem>
                {/* Page numbers */}
                {(() => {
                  const totalPages = Math.max(1, Math.ceil(count / pageSize));
                  const items = [];
                  let start = Math.max(1, page - 1);
                  let end = Math.min(totalPages, page + 1);
                  if (page === 1) end = Math.min(totalPages, 3);
                  if (page === totalPages) start = Math.max(1, totalPages - 2);
                  for (let i = start; i <= end; i++) {
                    items.push(
                      <PaginationItem key={i}>
                        <PaginationLink
                          href="#"
                          isActive={i === page}
                          onClick={(e) => {
                            e.preventDefault();
                            setPage(i);
                          }}
                        >
                          {i}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  }
                  if (start > 1) {
                    items.unshift(
                      <PaginationItem key="start-ellipsis">
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                    items.unshift(
                      <PaginationItem key={1}>
                        <PaginationLink
                          href="#"
                          isActive={1 === page}
                          onClick={(e) => {
                            e.preventDefault();
                            setPage(1);
                          }}
                        >
                          1
                        </PaginationLink>
                      </PaginationItem>
                    );
                  }
                  if (end < totalPages) {
                    items.push(
                      <PaginationItem key="end-ellipsis">
                        <PaginationEllipsis />
                      </PaginationItem>
                    );
                    items.push(
                      <PaginationItem key={totalPages}>
                        <PaginationLink
                          href="#"
                          isActive={totalPages === page}
                          onClick={(e) => {
                            e.preventDefault();
                            setPage(totalPages);
                          }}
                        >
                          {totalPages}
                        </PaginationLink>
                      </PaginationItem>
                    );
                  }
                  return items;
                })()}
                <PaginationItem>
                  <PaginationNext
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      const totalPages = Math.max(
                        1,
                        Math.ceil(count / pageSize)
                      );
                      if (page < totalPages) setPage(page + 1);
                    }}
                    aria-disabled={page >= Math.ceil(count / pageSize)}
                  />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          </div>
        </div>
      </div>

      <EditDeviceDialog
        isOpen={editDialogOpen}
        onClose={handleCloseEditDialog}
        onSave={handleSaveDevice}
        device={selectedDevice}
        isLoading={editLoading}
      />
    </ProtectedRoute>
  );
};
