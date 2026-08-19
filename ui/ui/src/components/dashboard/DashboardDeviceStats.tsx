"use client";

import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { useAuth } from "@/context/authContext";
import { fetchSwitches } from "@/lib/devices";
import { fetchDeviceStatsAggregate } from "@/lib/deviceStats";
import { DeviceStatsChart } from "../graphs/device-stats/DeviceStatsChart";
import { NetworkDeviceDetails, DeviceStatsTimeSeriesPoint } from "@/lib/types";
import { DeviceStatsSkeleton } from "../graphs/device-stats/DeviceStatsSkeleton";

export default function DashboardDeviceStats() {
  const { token } = useAuth();
  const [data, setData] = useState<DeviceStatsTimeSeriesPoint[]>([]);
  const [device, setDevice] = useState<NetworkDeviceDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    const abortController = new AbortController();
    let isMounted = true;
    const load = async () => {
      try {
        setLoading(true);
        // 1. Get first switch
        const switches = await fetchSwitches(token);
        
        // handle paginated or array response
        let devices: NetworkDeviceDetails[] = [];
        if (Array.isArray(switches)) {
          devices = switches;
        } else if (switches && typeof switches === 'object' && 'results' in switches) {
          const results = (switches as { results: NetworkDeviceDetails[] }).results;
          devices = Array.isArray(results) ? results : [];
        }

        if (devices.length === 0) {
          if (!isMounted) return;
          setDevice(null);
          setData([]);
          return;
        }

        // Try each device until we find one with stats data
        let foundDeviceWithData = false;
        for (const device of devices) {
          if (!device.lan_ip_address) {
            continue;
          }
          
          try {
            const stats = await fetchDeviceStatsAggregate(
              token,
              device.lan_ip_address,
              1, // 1 hour
              "1 minute",
              abortController.signal
            );
            
            if (stats && stats.data && Array.isArray(stats.data) && stats.data.length > 0) {
              if (!isMounted) return;
              setDevice(device);
              setData(stats.data);
              foundDeviceWithData = true;
              break;
            }
          } catch (statsError) {
            if (abortController.signal.aborted) return;
            console.error(`[DashboardDeviceStats] Error fetching stats for ${device.lan_ip_address}:`, statsError);
            continue;
          }
        }

        if (!foundDeviceWithData) {
          // Still set the first device so we can show which device we checked
          if (!isMounted) return;
          setDevice(devices[0]);
          setData([]);
        }
      } catch (e) {
        if (abortController.signal.aborted) return;
        console.error("Failed to load device stats for dashboard", e);
        if (e instanceof Error) {
          console.error("Error details:", e.message, e.stack);
        }
        if (!isMounted) return;
        setData([]);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    load();
    // Refresh every minute like the other charts
    const interval = setInterval(load, 60000);
    return () => {
      isMounted = false;
      abortController.abort();
      clearInterval(interval);
    };
  }, [token]);

  if (loading) {
    return <DeviceStatsSkeleton />;
  }

  if (!device) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Device Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center min-h-[300px] text-muted-foreground">
            No monitored devices found.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Device Statistics</CardTitle>
        <CardDescription>
          {device.name || device.lan_ip_address}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <div className="flex items-center justify-center min-h-[400px] text-muted-foreground">
            <div className="text-center">
              <p>No device statistics data available for the last hour.</p>
              <p className="text-sm mt-2">
                Device: {device.lan_ip_address}
              </p>
            </div>
          </div>
        ) : (
          <>
            <div className="text-xs text-muted-foreground mb-2">
              Showing {data.length} data points for {device.lan_ip_address}
            </div>
            <DeviceStatsChart data={data} />
          </>
        )}
      </CardContent>
    </Card>
  );
}

