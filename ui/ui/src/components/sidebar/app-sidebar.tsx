"use client";

import * as React from "react";

import { NavMain } from "@/components/sidebar/nav-main";
import { NavUser } from "@/components/sidebar/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

import { useAuth } from "@/context/authContext";
import { usePluginContext } from "@/context/PluginContext";
import { useLanguage } from "@/context/languageContext";
import { buildSidebarConfig } from "@/lib/sidebarConfig";
import Image from "next/image";
import { NotificationPanel } from "@/components/notifications/NotificationPanel";

/**
 * Render the application sidebar with branding, plugin-aware navigation, user details, and notifications.
 *
 * The component builds the main navigation from installed plugins and localization, then renders a Sidebar
 * with a branded header linking to the dashboard, the main navigation, and a footer showing the current user
 * and a notification panel.
 *
 * @param props - Props forwarded to the root Sidebar component
 * @returns The Sidebar React element populated with header, main navigation, and footer content
 */
export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { username } = useAuth();
  const { installedPlugins } = usePluginContext();
  const { getT } = useLanguage();
  
  const navMain = buildSidebarConfig(installedPlugins, getT);

  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <a href="/dashboard">
                <div className="bg-sidebar-secondary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg">
                  <Image src="/logo.png" alt="Logo" width={32} height={32} />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">
                    {getT("sidebar.company_name")}
                  </span>
                  <span className="truncate text-xs">
                    {getT("sidebar.product_name")}
                  </span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
      </SidebarContent>
      <SidebarFooter>
        <div className="flex flex-col gap-2 p-2">
          <div className="flex items-center justify-between">
            <NavUser
              user={{
                name: username || getT("sidebar.default_user"),
                email: `${username}@example.com`,
                avatar: "/icons/profile-picture.png",
              }}
            />
            <NotificationPanel />
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}