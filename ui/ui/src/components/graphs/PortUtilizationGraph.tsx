/*
 * File: PortUtilizationGraph.tsx
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

import React, { useEffect, useState, useCallback } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useLanguage } from "@/context/languageContext";
import { useAuth } from "@/context/authContext";
import {
  fetchAllDevicesPortStats,
  fetchPortStatsAggregate,
} from "@/lib/portUtilization";
import { DevicePortData, AggregateTimeSeriesPoint } from "@/lib/types";
import { DeviceSelector } from "./port-utilization/DeviceSelector";
import { PortFilter } from "./port-utilization/PortFilter";
import { TimeRangeSelector } from "./port-utilization/TimeRangeSelector";
import { PortUtilizationChart } from "./port-utilization/PortUtilizationChart";
import { PortUtilizationSkeleton } from "./port-utilization/PortUtilizationSkeleton";

export default function PortUtilizationGraph() {
  const { getT } = useLanguage();
  const { token } = useAuth();

  // State
  const [devices, setDevices] = useState<DevicePortData[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");
  const [availablePorts, setAvailablePorts] = useState<string[]>([]);
  const [selectedPorts, setSelectedPorts] = useState<string[]>([]);
  const [selectedHours, setSelectedHours] = useState<number>(15 / 60); // 15 minutes default
  const [selectedInterval, setSelectedInterval] =
    useState<string>("10 seconds");
  const [aggregateData, setAggregateData] = useState<
    AggregateTimeSeriesPoint[]
  >([]);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all devices on mount
  useEffect(() => {
    const loadDevices = async () => {
      if (!token) return;

      try {
        setIsInitialLoading(true);
        setError(null);
        const response = await fetchAllDevicesPortStats(token, 24); // Get 24h for device list
        const deviceList = Object.values(response.devices);
        setDevices(deviceList);

        // Auto-select "all" devices by default
        setSelectedDevice("all");
      } catch (err) {
        console.error("Error fetching devices:", err);
        setError(
          getT("page.PortUtilizationPage.no_devices", "No devices found")
        );
      } finally {
        setIsInitialLoading(false);
      }
    };

    loadDevices();
  }, [token, getT]);

  // Fetch port data when device or time range changes
  const loadPortData = useCallback(async () => {
    if (!token || !selectedDevice) return;

    try {
      setIsLoading(true);
      setError(null);

      // Determine IP address to query (null for all devices)
      const ipAddress = selectedDevice === "all" ? null : selectedDevice;

      // Fetch aggregate data using the new endpoint
      const response = await fetchPortStatsAggregate(
        token,
        ipAddress,
        selectedHours,
        selectedInterval
      );

      setAggregateData(response.aggregated_data);

      // Extract unique port names from the data
      const portKeys = new Set<string>();
      response.aggregated_data.forEach((point) => {
        const portKey = `${point.ip_address} - ${point.port_name}`;
        portKeys.add(portKey);
      });

      setAvailablePorts(Array.from(portKeys));

      // Reset port filter to "all" when device changes
      setSelectedPorts([]);
    } catch (err) {
      console.error("Error fetching port data:", err);
      setError(
        getT("page.PortUtilizationPage.no_data", "No port data available")
      );
      setAggregateData([]);
      setAvailablePorts([]);
    } finally {
      setIsLoading(false);
    }
  }, [token, selectedDevice, selectedHours, selectedInterval, getT]);

  // Load port data when dependencies change
  useEffect(() => {
    if (selectedDevice) {
      loadPortData();
    }
  }, [selectedDevice, selectedHours, selectedInterval, loadPortData]);

  // Show skeleton on initial load
  if (isInitialLoading) {
    return <PortUtilizationSkeleton />;
  }

  // Show error if no devices
  if (devices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {getT("page.PortUtilizationPage.page_title", "Port Utilization")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-destructive mb-2">
                {getT(
                  "page.PortUtilizationPage.no_devices",
                  "No devices found"
                )}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {getT("page.PortUtilizationPage.page_title", "Port Utilization")}
        </CardTitle>
        <CardDescription>
          <div className="space-y-3">
            <p className="text-sm">
              {getT(
                "page.PortUtilizationPage.description",
                "View utilization and throughput for your network devices"
              )}
            </p>
            <div className="flex gap-3 flex-wrap items-center">
              <DeviceSelector
                devices={devices}
                selectedDevice={selectedDevice}
                onChange={setSelectedDevice}
              />
              <PortFilter
                ports={availablePorts}
                selectedPorts={selectedPorts}
                onChange={setSelectedPorts}
              />
              <TimeRangeSelector
                selectedHours={selectedHours}
                onHoursChange={(hours, interval) => {
                  setSelectedHours(hours);
                  setSelectedInterval(interval);
                }}
              />
            </div>
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span className="text-muted-foreground">
                {getT(
                  "page.PortUtilizationPage.loading",
                  "Loading port statistics..."
                )}
              </span>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-destructive mb-2">Error loading data</p>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </div>
        ) : aggregateData.length === 0 ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground">
                {getT(
                  "page.PortUtilizationPage.no_data",
                  "No port data available"
                )}
              </p>
            </div>
          </div>
        ) : (
          <PortUtilizationChart
            data={aggregateData}
            selectedPorts={selectedPorts}
          />
        )}
      </CardContent>
    </Card>
  );
}
