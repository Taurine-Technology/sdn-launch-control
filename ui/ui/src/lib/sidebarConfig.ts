import {
  Brain,
  ChartColumnIncreasing,
  Network,
  Settings2,
  LucideIcon,
} from "lucide-react";
import type { PluginInstallation } from "@/lib/types";

export interface SidebarNavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  items?: { title: string; url: string }[];
}

/**
 * Build the sidebar navigation configuration based on installed plugins and translations.
 *
 * @param installedPlugins - List of installed plugin records used to determine conditional sections
 * @param getT - Translation function that maps a localization key and optional fallback to a string
 * @returns An array of sidebar navigation items; includes an "AI Services" section only if relevant plugins are installed
 */
export function buildSidebarConfig(
  installedPlugins: PluginInstallation[],
  getT: (key: string, fallback?: string) => string
): SidebarNavItem[] {
  const showTrafficPlugin = installedPlugins.some(
    (p) => p.plugin_name === "tau-onos-metre-traffic-classification"
  );

  const showSnifferPlugin = installedPlugins.some(
    (p) => p.plugin_name === "tau-traffic-classification-sniffer"
  );

  return [
    {
      title: getT("navigation.network"),
      url: "/dashboard",
      icon: Network,
      isActive: true,
      items: [
        {
          title: getT("navigation.devices_overview"),
          url: "/devices/overview",
        },
        { title: getT("navigation.switches"), url: "/devices/switches" },
        { title: getT("navigation.controllers"), url: "/devices/controllers" },
        { title: "Network Notifications", url: "/network-notifications" },
      ],
    },
    {
      title: getT("navigation.monitoring"),
      url: "/monitoring/classifications",
      icon: ChartColumnIncreasing,
      items: [
        {
          title: getT("navigation.traffic_classification"),
          url: "/monitoring/classifications",
        },
      ],
    },
    ...(showTrafficPlugin || showSnifferPlugin
      ? [
          {
            title: getT("navigation.ai_services"),
            url: "/plugins/tau-odl-metre-traffic-classification",
            icon: Brain,
            items: [
              ...(showTrafficPlugin
                ? [
                    {
                      title: getT("navigation.traffic_classification_plugin"),
                      url: "/plugins/tau-odl-metre-traffic-classification",
                    },
                    {
                      title: getT("navigation.model_management"),
                      url: "/plugins/model-management",
                    },
                  ]
                : []),
              ...(showSnifferPlugin
                ? [
                    {
                      title: getT("navigation.sniffer_management"),
                      url: "/plugins/sniffer-management",
                    },
                  ]
                : []),
            ],
          },
        ]
      : []),
    {
      title: getT("navigation.settings"),
      url: "/account",
      icon: Settings2,
      items: [
        { title: getT("navigation.plugins"), url: "/plugins" },
        { title: getT("navigation.notifications"), url: "/notifications" },
      ],
    },
  ];
}