"use client";
import React, {
  createContext,
  useState,
  useContext,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { createAxiosInstanceWithToken } from "@/lib/axiosInstance";
import { NetworkMapData, NetworkNode, NetworkLink } from "@/lib/types";

interface NetworkContextType {
  networkData: NetworkMapData;
  isRefreshing: boolean;
  error: string | null;
  fetchNetworkMap: (isInitialLoad?: boolean) => Promise<void>;
  resetNetworkData: () => void;
}

const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

const NETWORK_MAP_CACHE_KEY = "sdnLaunchControlNetworkMapCache";

function processNetworkData(data: Record<string, { bridges: Array<{ name: string; flows?: Array<{ dl_src?: string; dl_dst?: string }>; controller_name?: string }> }>): NetworkMapData {
  const nodes: NetworkNode[] = [];
  const links: NetworkLink[] = [];
  const linkSet = new Set<string>();
  const nodeSet = new Set<string>();

  const addUniqueNode = (node: NetworkNode) => {
    if (!node || !node.id) return;
    if (nodeSet.has(node.id)) return;
    nodes.push(node);
    nodeSet.add(node.id);
  };

  Object.entries(data || {}).forEach(
    ([hostName, switchInfo]: [string, { bridges: Array<{ name: string; flows?: Array<{ dl_src?: string; dl_dst?: string }>; controller_name?: string }> }]) => {
      if (!Array.isArray(switchInfo.bridges)) return;
      switchInfo.bridges.forEach((bridge: { name: string; flows?: Array<{ dl_src?: string; dl_dst?: string }>; controller_name?: string }) => {
        if (!bridge || !bridge.name) return;
        const bridgeNodeId = `${hostName}-${bridge.name}`;
        addUniqueNode({
          id: bridgeNodeId,
          type: "switch",
          hostName,
          bridgeName: bridge.name,
        });
        bridge.flows?.forEach((flow: { dl_src?: string; dl_dst?: string }) => {
          if (!flow) return;
          if (flow.dl_src) {
            addUniqueNode({ id: flow.dl_src, type: "device" });
            const key = `${flow.dl_src}-${bridgeNodeId}`;
            const revKey = `${bridgeNodeId}-${flow.dl_src}`;
            if (
              nodeSet.has(flow.dl_src) &&
              nodeSet.has(bridgeNodeId) &&
              !linkSet.has(key) &&
              !linkSet.has(revKey)
            ) {
              links.push({ source: flow.dl_src, target: bridgeNodeId });
              linkSet.add(key);
            }
          }
          if (flow.dl_dst) {
            addUniqueNode({ id: flow.dl_dst, type: "device" });
            const key = `${bridgeNodeId}-${flow.dl_dst}`;
            const revKey = `${flow.dl_dst}-${bridgeNodeId}`;
            if (
              nodeSet.has(bridgeNodeId) &&
              nodeSet.has(flow.dl_dst) &&
              !linkSet.has(key) &&
              !linkSet.has(revKey)
            ) {
              links.push({ source: bridgeNodeId, target: flow.dl_dst });
              linkSet.add(key);
            }
          }
        });
        if (bridge.controller_name) {
          addUniqueNode({ id: bridge.controller_name, type: "controller" });
          const key = `${bridgeNodeId}-${bridge.controller_name}`;
          const revKey = `${bridge.controller_name}-${bridgeNodeId}`;
          if (
            nodeSet.has(bridgeNodeId) &&
            nodeSet.has(bridge.controller_name) &&
            !linkSet.has(key) &&
            !linkSet.has(revKey)
          ) {
            links.push({
              source: bridgeNodeId,
              target: bridge.controller_name,
            });
            linkSet.add(key);
          }
        }
      });
    }
  );
  // Final check
  const finalNodeIds = new Set(nodes.map((n) => n.id));
  const validLinks = links.filter(
    (link) => finalNodeIds.has(link.source) && finalNodeIds.has(link.target)
  );
  return { nodes, links: validLinks };
}

export const NetworkProvider = ({ children }: { children: ReactNode }) => {
  const [networkData, setNetworkData] = useState<NetworkMapData>({
    nodes: [],
    links: [],
  });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNetworkMap = useCallback(async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const token = localStorage.getItem("taurineToken");
      const axiosInstance = createAxiosInstanceWithToken(token || "");
      const { data } = await axiosInstance.get("/ovs-network-map/");
      if (!data.data || Object.keys(data.data).length === 0) {
        setNetworkData({ nodes: [], links: [] });
        sessionStorage.removeItem(NETWORK_MAP_CACHE_KEY);
        setError("No network data found.");
      } else {
        const processedData = processNetworkData(data.data);
        setNetworkData(processedData);
        try {
          sessionStorage.setItem(
            NETWORK_MAP_CACHE_KEY,
            JSON.stringify(processedData)
          );
        } catch {
          setError("Failed to cache network data.");
        }
      }
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to fetch network map.");
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    try {
      const cachedDataString = sessionStorage.getItem(NETWORK_MAP_CACHE_KEY);
      if (cachedDataString) {
        const cachedData = JSON.parse(cachedDataString);
        if (
          cachedData &&
          Array.isArray(cachedData.nodes) &&
          Array.isArray(cachedData.links)
        ) {
          if (isMounted) {
            setNetworkData(cachedData);
          }
        } else {
          sessionStorage.removeItem(NETWORK_MAP_CACHE_KEY);
        }
      }
    } catch {
      sessionStorage.removeItem(NETWORK_MAP_CACHE_KEY);
    } finally {
    }
    return () => {
      isMounted = false;
    };
  }, []);

  const value: NetworkContextType = {
    networkData,
    isRefreshing,
    error,
    fetchNetworkMap,
    resetNetworkData: () => {
      setNetworkData({ nodes: [], links: [] });
      sessionStorage.removeItem(NETWORK_MAP_CACHE_KEY);
    },
  };

  return (
    <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>
  );
};

export const useNetwork = (): NetworkContextType => {
  const context = useContext(NetworkContext);
  if (!context) {
    throw new Error("useNetwork must be used within a NetworkProvider");
  }
  return context;
};
