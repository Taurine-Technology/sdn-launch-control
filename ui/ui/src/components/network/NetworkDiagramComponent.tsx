"use client";
import React, { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";
import { Card } from "@/components/ui/card";
import { useNetwork } from "@/context/NetworkContext";
import { useLanguage } from "@/context/languageContext";

import { fetchNetworkDevices } from "@/lib/devices";
import { fetchNetworkDevice } from "@/lib/networkDevice";
import { NetworkNode, NetworkMapData, NetworkDeviceDetails } from "@/lib/types";

import { RingLoader } from "react-spinners";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "../ui/skeleton";

const icons: Record<string, string> = {
  switch: "/icons/switch.png",
  controller: "/icons/controller.png",
  access_point: "/icons/access_point.png",
  device: "/icons/person.png",
  default: "/icons/person.png",
};

export const NetworkDiagramComponent: React.FC = () => {
  const { networkData, error, fetchNetworkMap } = useNetwork();
  const { getT } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [deviceDetails, setDeviceDetails] =
    useState<NetworkDeviceDetails | null>(null);
  const [deviceDetailsLoading, setDeviceDetailsLoading] = useState(false);
  const [deviceDetailsError, setDeviceDetailsError] = useState("");
  const d3Container = useRef<SVGSVGElement | null>(null);
  const svgContainerRef = useRef<HTMLDivElement | null>(null);
  // Popover anchor position state
  const [popoverPos, setPopoverPos] = useState<{ x: number; y: number } | null>(
    null
  );

  // Helper function to map device types like in DeviceOverviewTable
  const getDeviceTypeLabel = (deviceType: string): string => {
    switch (deviceType) {
      case "end_user":
        return getT("page.DevicesOverviewPage.end_user");
      case "switch":
        return getT("page.DevicesOverviewPage.switch");
      case "access_point":
        return getT("page.DevicesOverviewPage.access_point");
      case "server":
        return getT("page.DevicesOverviewPage.server");
      case "controller":
        return getT("page.DevicesOverviewPage.controller");
      case "vm":
        return getT("page.DevicesOverviewPage.vm");
      default:
        return deviceType;
    }
  };

  // Helper function to map operating systems like in DeviceOverviewTable
  const getOperatingSystemLabel = (os: string): string => {
    switch (os) {
      case "ubuntu_22_server":
        return "Ubuntu Server 22";
      default:
        return os;
    }
  };

  useEffect(() => {
    // console.log("[NETWORKDIAGRAMCOMPONENT] fetching network map");

    const fetchData = async () => {
      try {
        setIsLoading(true);
        await fetchNetworkMap();
      } catch (error) {
        console.error("[NETWORKDIAGRAMCOMPONENT] error", error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [fetchNetworkMap]);

  const drawDiagram = useCallback(
    (data: NetworkMapData) => {
      if (!d3Container.current || !svgContainerRef.current) return;
      const svg = d3.select(d3Container.current);
      svg.selectAll("*").remove();
      const container = svgContainerRef.current;
      const width = container.clientWidth || 600;
      const height = container.clientHeight || 400;
      svg.attr("width", width).attr("height", height);
      if (!data.nodes.length) {
        svg
          .append("text")
          .attr("x", width / 2)
          .attr("y", height / 2)
          .attr("text-anchor", "middle")
          .attr("fill", "#ccc")
          .style("font-size", "16px")
          .text(
            error
              ? error
              : getT("components.network.network_diagram.no_devices")
          );
        return;
      }
      const simulation = d3
        .forceSimulation(data.nodes as d3.SimulationNodeDatum[])
        .force(
          "link",
          d3
            .forceLink(
              data.links as d3.SimulationLinkDatum<d3.SimulationNodeDatum>[]
            )
            .id((d: d3.SimulationNodeDatum) => (d as NetworkNode).id)
            .distance(120)
            .strength(0.6)
        )
        .force("charge", d3.forceManyBody().strength(-50))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(25));
      const link = svg
        .append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(data.links)
        .enter()
        .append("line")
        .attr("stroke-width", 3)
        .attr("stroke", "#7456FD")
        .attr("stroke-opacity", 0.7);
      const node = svg
        .append("g")
        .attr("class", "nodes")
        .selectAll("g")
        .data(data.nodes as d3.SimulationNodeDatum[])
        .enter()
        .append("g")
        .call(
          d3
            .drag<SVGGElement, d3.SimulationNodeDatum>()
            .on(
              "start",
              (
                event: d3.D3DragEvent<
                  SVGGElement,
                  d3.SimulationNodeDatum,
                  d3.SimulationNodeDatum
                >
              ) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
              }
            )
            .on(
              "drag",
              (
                event: d3.D3DragEvent<
                  SVGGElement,
                  d3.SimulationNodeDatum,
                  d3.SimulationNodeDatum
                >
              ) => {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
              }
            )
            .on(
              "end",
              (
                event: d3.D3DragEvent<
                  SVGGElement,
                  d3.SimulationNodeDatum,
                  d3.SimulationNodeDatum
                >
              ) => {
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
              }
            )
        )
        .on("click", (event: MouseEvent, d: d3.SimulationNodeDatum) =>
          handleNodeClick(event, d as NetworkNode)
        );
      node
        .append("image")
        .attr(
          "href",
          (d: d3.SimulationNodeDatum) =>
            icons[(d as { type: string }).type] || icons.default
        )
        .attr("width", 40)
        .attr("height", 40)
        .attr("x", -20)
        .attr("y", -20);
      node
        .append("title")
        .text(
          (d: d3.SimulationNodeDatum) =>
            (d as { displayName?: string; id: string }).displayName ||
            (d as { id: string }).id
        );
      simulation.on("tick", () => {
        const constrain = (val: number, min: number, max: number) =>
          Math.max(min, Math.min(max, val));
        const radius = 25;
        link
          .attr(
            "x1",
            (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
              (d.source as d3.SimulationNodeDatum).x ?? 0
          )
          .attr(
            "y1",
            (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
              (d.source as d3.SimulationNodeDatum).y ?? 0
          )
          .attr(
            "x2",
            (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
              (d.target as d3.SimulationNodeDatum).x ?? 0
          )
          .attr(
            "y2",
            (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
              (d.target as d3.SimulationNodeDatum).y ?? 0
          );
        node.attr("transform", (d: d3.SimulationNodeDatum) => {
          d.x = constrain(d.x ?? 0, radius, width - radius);
          d.y = constrain(d.y ?? 0, radius, height - radius);
          return `translate(${d.x},${d.y})`;
        });
      });
      svg.on("click", () => setSelectedNode(null));
    },
    [error, getT]
  );

  useEffect(() => {
    if (!isLoading && d3Container.current && svgContainerRef.current) {
      drawDiagram(networkData);
    }
    const handleResize = () => {
      if (!isLoading && d3Container.current && svgContainerRef.current) {
        drawDiagram(networkData);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [networkData, drawDiagram, isLoading]);

  useEffect(() => {
    const fetchDetails = async () => {
      setDeviceDetails(null);
      setDeviceDetailsError("");
      if (!selectedNode || selectedNode.type !== "device") return;
      setDeviceDetailsLoading(true);
      try {
        const token = localStorage.getItem("taurineToken") || "";
        const data = await fetchNetworkDevices(token);
        let found = null;
        if (
          Array.isArray((data as { results: NetworkDeviceDetails[] }).results)
        ) {
          found = (data as { results: NetworkDeviceDetails[] }).results.find(
            (d: NetworkDeviceDetails) =>
              d.mac_address &&
              d.mac_address.toLowerCase() === selectedNode.id.toLowerCase()
          );
        } else if (Array.isArray(data)) {
          found = (data as NetworkDeviceDetails[]).find(
            (d: NetworkDeviceDetails) =>
              d.mac_address &&
              d.mac_address.toLowerCase() === selectedNode.id.toLowerCase()
          );
        }
        if (found) {
          const fullDetails = await fetchNetworkDevice(token, found.id);
          setDeviceDetails({
            ...fullDetails,
            id: fullDetails.id.toString(),
          });
        } else {
          setDeviceDetailsError(
            getT(
              "components.network.network_diagram.device_not_found",
              "Device details not found."
            )
          );
        }
      } catch {
        setDeviceDetailsError(
          getT(
            "components.network.network_diagram.fetch_error",
            "Failed to fetch device details."
          )
        );
      } finally {
        setDeviceDetailsLoading(false);
      }
    };
    fetchDetails();
  }, [selectedNode, getT]);

  // Update popover position when a node is selected
  const handleNodeClick = (event: MouseEvent, d: d3.SimulationNodeDatum) => {
    event.stopPropagation();
    setSelectedNode(d as NetworkNode);
    // Get SVG position relative to viewport
    if (svgContainerRef.current) {
      const rect = svgContainerRef.current.getBoundingClientRect();
      // Use d.x/d.y for node position, fallback to center if missing
      setPopoverPos({
        x: rect.left + (d.x ?? rect.width / 2),
        y: rect.top + (d.y ?? rect.height / 2),
      });
    }
  };

  // Popover trigger: invisible button absolutely positioned at popoverPos
  const popoverTrigger = popoverPos && (
    <button
      style={{
        position: "fixed",
        left: popoverPos.x,
        top: popoverPos.y,
        width: 1,
        height: 1,
        opacity: 0,
        pointerEvents: "none",
      }}
      aria-label="Node Details Trigger"
      tabIndex={-1}
    />
  );

  return (
    <Card className="m-4 shadow-lg">
      <div
        ref={svgContainerRef}
        className="w-full min-h-[400px] flex justify-center items-center"
      >
        {isLoading ? (
          <div className="relative w-full h-[400px]">
            <Skeleton className="h-[400px] w-full bg-card" />
            <div className="absolute inset-0 flex items-center justify-center">
              <RingLoader color="#7456FD" size={60} loading={true} />
            </div>
          </div>
        ) : (
          <svg ref={d3Container} />
        )}
      </div>
      {error && !isLoading && (
        <div className="flex justify-center p-2">
          <div className="text-destructive bg-destructive/10 rounded px-4 py-2 w-3/4 text-center">
            {error}
          </div>
        </div>
      )}
      <Popover
        open={!!selectedNode}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedNode(null);
            setPopoverPos(null);
          }
        }}
      >
        <PopoverTrigger asChild>{popoverTrigger}</PopoverTrigger>
        <PopoverContent
          className="bg-background mt-5"
          side="right"
          align="start"
          style={{ zIndex: 50, minWidth: 280 }}
        >
          {selectedNode && (
            <div className="space-y-2">
              <div>
                <b>{getT("common.name")}:</b> {selectedNode.id}
              </div>
              <div>
                <b>{getT("common.type")}:</b> {selectedNode.type}
              </div>
              {selectedNode.type === "switch" && selectedNode.hostName && (
                <div>
                  <b>{getT("common.name")}:</b> {selectedNode.hostName}
                </div>
              )}
              {selectedNode.type === "switch" && selectedNode.bridgeName && (
                <div>
                  <b>{getT("components.devices.bridge_data.bridge_name")}:</b>{" "}
                  {selectedNode.bridgeName}
                </div>
              )}
              {selectedNode.type === "device" && (
                <>
                  {deviceDetailsLoading ? (
                    <div className="flex items-center gap-2">
                      <RingLoader color="#7456FD" size={20} loading={true} />{" "}
                      {getT("common.loading")}
                    </div>
                  ) : deviceDetailsError ? (
                    <div className="text-destructive">{deviceDetailsError}</div>
                  ) : deviceDetails ? (
                    <>
                      <div>
                        <b>{getT("common.name")}:</b> {deviceDetails.name}
                      </div>
                      <div>
                        <b>{getT("common.mac_address")}:</b>{" "}
                        {deviceDetails.mac_address}
                      </div>
                      <div>
                        <b>{getT("common.ip_address")}:</b>{" "}
                        {deviceDetails.ip_address}
                      </div>
                      <div>
                        <b>{getT("common.device_type")}:</b>{" "}
                        {getDeviceTypeLabel(deviceDetails.device_type || "")}
                      </div>
                      <div>
                        <b>{getT("common.operating_system")}:</b>{" "}
                        {getOperatingSystemLabel(
                          deviceDetails.operating_system || ""
                        )}
                      </div>
                      <div>
                        <b>{getT("common.verified")}:</b>{" "}
                        {deviceDetails.verified
                          ? getT("common.yes")
                          : getT("common.no")}
                      </div>
                    </>
                  ) : null}
                </>
              )}
            </div>
          )}
        </PopoverContent>
      </Popover>
    </Card>
  );
};

export default NetworkDiagramComponent;
