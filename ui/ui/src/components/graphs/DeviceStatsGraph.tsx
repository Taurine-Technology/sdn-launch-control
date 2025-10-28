/**
 * File: DeviceStatsGraph.tsx
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
import { fetchSwitches } from "@/lib/devices";
import { fetchDeviceStatsAggregate } from "@/lib/deviceStats";
import { NetworkDeviceDetails, DeviceStatsTimeSeriesPoint } from "@/lib/types";
import { DeviceStatsDeviceSelector } from "./device-stats/DeviceStatsDeviceSelector";
import {
  TimeRangeSelector,
  getIntervalForHours,
} from "./port-utilization/TimeRangeSelector";
import { DeviceStatsChart } from "./device-stats/DeviceStatsChart";
import { DeviceStatsSkeleton } from "./device-stats/DeviceStatsSkeleton";

export default function DeviceStatsGraph() {
  const { getT } = useLanguage();
  const { token } = useAuth();

  const [devices, setDevices] = useState<NetworkDeviceDetails[]>([]);
  const [selectedIp, setSelectedIp] = useState<string>("");
  const [selectedHours, setSelectedHours] = useState<number>(1); // default 1 hour
  const [interval, setInterval] = useState<string>("10 seconds");
  const [data, setData] = useState<DeviceStatsTimeSeriesPoint[]>([]);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load switches
  useEffect(() => {
    const load = async () => {
      if (!token) return;
      try {
        setIsInitialLoading(true);
        setError(null);
        const resp = await fetchSwitches(token);
        const results = Array.isArray(resp) ? resp : resp.results || [];
        setDevices(results);
        if (results.length > 0) {
          setSelectedIp(
            (results[0].lan_ip_address as string) || results[0].ip_address || ""
          );
        }
      } catch (e) {
        console.error("Error fetching switches", e);
        setError(getT("page.DeviceStatsPage.no_devices", "No switches found"));
      } finally {
        setIsInitialLoading(false);
      }
    };
    load();
  }, [token, getT]);

  const loadStats = useCallback(
    async (signal?: AbortSignal) => {
      if (!token || !selectedIp) return;
      try {
        setIsLoading(true);
        setError(null);
        const resp = await fetchDeviceStatsAggregate(
          token,
          selectedIp,
          selectedHours,
          interval,
          signal
        );
        if (signal?.aborted) return;
        setData(resp.data);
      } catch (e) {
        if (signal?.aborted) return;
        console.error("Error fetching device stats", e);
        setError(
          getT("page.DeviceStatsPage.no_data", "No device stats available")
        );
        setData([]);
      } finally {
        if (!signal?.aborted) setIsLoading(false);
      }
    },
    [token, selectedIp, selectedHours, interval, getT]
  );

  // Refresh when dependencies change
  useEffect(() => {
    if (!selectedIp) return;
    const ac = new AbortController();
    loadStats(ac.signal);
    return () => ac.abort();
  }, [selectedIp, selectedHours, interval, loadStats]);

  // Initial skeleton
  if (isInitialLoading) {
    return <DeviceStatsSkeleton />;
  }

  // Empty state
  if (devices.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {getT("page.DeviceStatsPage.page_title", "Device Stats")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-destructive mb-2">
                {getT("page.DeviceStatsPage.no_devices", "No switches found")}
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
          {getT("page.DeviceStatsPage.page_title", "Device Stats")}
        </CardTitle>
        <CardDescription>
          <div className="flex gap-3 flex-wrap items-center">
            <DeviceStatsDeviceSelector
              devices={devices}
              selectedIp={selectedIp}
              onChange={setSelectedIp}
            />
            <TimeRangeSelector
              selectedHours={selectedHours}
              onHoursChange={(h) => {
                setSelectedHours(h);
                setInterval(getIntervalForHours(h));
              }}
            />
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
                  "page.DeviceStatsPage.loading",
                  "Loading device stats..."
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
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <p className="text-muted-foreground">
                {getT(
                  "page.DeviceStatsPage.no_data",
                  "No device stats available"
                )}
              </p>
            </div>
          </div>
        ) : (
          <DeviceStatsChart data={data} />
        )}
      </CardContent>
    </Card>
  );
}
