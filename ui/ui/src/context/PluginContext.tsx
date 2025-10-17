"use client";
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from "react";
import { fetchInstalledPlugins } from "@/lib/software";
import type { PluginInstallation } from "@/lib/types";
import { useAuth } from "@/context/authContext";

interface PluginContextType {
  installedPlugins: PluginInstallation[];
  loadInstalledPlugins: () => Promise<void>;
  loading: boolean;
}

const PluginContext = createContext<PluginContextType | undefined>(undefined);

export const PluginProvider = ({ children }: { children: ReactNode }) => {
  // Initialize from localStorage if available
  const [installedPlugins, setInstalledPlugins] = useState<
    PluginInstallation[]
  >(() => {
    if (typeof window !== "undefined") {
      try {
        const cached = localStorage.getItem("installed_plugins_cache");
        if (cached) {
          return JSON.parse(cached);
        }
      } catch {
        // ignore localStorage errors
      }
    }
    return [];
  });
  const [loading, setLoading] = useState(true);
  const { token, isAuthenticated } = useAuth();

  const loadInstalledPlugins = useCallback(async () => {
    setLoading(true);
    try {
      if (!token) {
        setInstalledPlugins([]);
        setLoading(false);
        return;
      }
      const installedPluginData = await fetchInstalledPlugins(token);
      // Add plugin_name for convenience
      const processedInstalledPlugins = installedPluginData.map(
        (installedPlugin) => ({
          ...installedPlugin,
          plugin_name: installedPlugin.plugin?.name || "Unknown Plugin",
        })
      );
      console.log(
        "[PluginContext.tsx] processedInstalledPlugins",
        processedInstalledPlugins
      );
      setInstalledPlugins(processedInstalledPlugins);
      
      // Cache the result in localStorage
      try {
        localStorage.setItem("installed_plugins_cache", JSON.stringify(processedInstalledPlugins));
      } catch {
        // ignore localStorage errors
      }
    } catch (error) {
      console.error("[PluginContext.tsx] loadInstalledPlugins", error);
      setInstalledPlugins([]);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (isAuthenticated && token) {
      loadInstalledPlugins();
    } else if (!isAuthenticated) {
      setInstalledPlugins([]);
      setLoading(false);
      // Clear cache when not authenticated
      try {
        localStorage.removeItem("installed_plugins_cache");
      } catch {
        // ignore localStorage errors
      }
    }
  }, [isAuthenticated, token, loadInstalledPlugins]);

  return (
    <PluginContext.Provider
      value={{ installedPlugins, loadInstalledPlugins, loading }}
    >
      {children}
    </PluginContext.Provider>
  );
};

export const usePluginContext = () => {
  const context = useContext(PluginContext);
  if (!context)
    throw new Error("usePluginContext must be used within a PluginProvider");
  return context;
};
