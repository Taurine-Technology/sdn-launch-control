"use client";
import * as React from "react";
import Link from "next/link";

import { ChevronRight, type LucideIcon } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { useLanguage } from "@/context/languageContext";

export function NavMain({
  items,
}: {
  items: {
    title: string;
    url: string;
    icon?: LucideIcon;
    isActive?: boolean;
    items?: {
      title: string;
      url: string;
      icon?: LucideIcon;
      items?: { title: string; url: string }[];
    }[];
  }[];
}) {
  const { getT } = useLanguage();

  // Persist open/closed state per top-level item title
  const storageKey = "sidebar_open_map";
  const initialMap: Record<string, boolean> = {};
  if (typeof window !== "undefined") {
    try {
      const saved = window.localStorage.getItem(storageKey);
      if (saved) Object.assign(initialMap, JSON.parse(saved));
    } catch {
      // ignore storage errors
    }
  }
  const [openMap, setOpenMap] =
    React.useState<Record<string, boolean>>(initialMap);

  const setItemOpen = (title: string, next: boolean) => {
    setOpenMap((prev) => {
      const updated = { ...prev, [title]: next };
      if (typeof window !== "undefined") {
        try {
          window.localStorage.setItem(storageKey, JSON.stringify(updated));
        } catch {
          // ignore
        }
      }
      return updated;
    });
  };

  return (
    <SidebarGroup>
      <SidebarMenu>
        {items.map((item) => {
          const hasChildren = !!item.items?.length;
          const isOpen = openMap[item.title] ?? item.isActive ?? false;
          const showPrimaryChild =
            hasChildren &&
            (item.url === "/dashboard" || item.url === "/account");
          const primaryChildLabel =
            item.url === "/dashboard"
              ? getT("navigation.dashboard", "Dashboard")
              : item.url === "/account"
              ? "Account"
              : item.title;

          return (
            <Collapsible
              key={item.title}
              asChild
              open={hasChildren ? isOpen : undefined}
              defaultOpen={hasChildren ? undefined : item.isActive}
              onOpenChange={(next) => {
                if (hasChildren) setItemOpen(item.title, next);
              }}
            >
              <SidebarMenuItem>
                {hasChildren ? (
                  <>
                    <CollapsibleTrigger asChild>
                      <SidebarMenuButton tooltip={item.title}>
                        {item.icon && <item.icon />}
                        <span>{item.title}</span>
                      </SidebarMenuButton>
                    </CollapsibleTrigger>
                    <CollapsibleTrigger asChild>
                      <SidebarMenuAction className="data-[state=open]:rotate-90">
                        <ChevronRight />
                        <span className="sr-only">
                          {getT("navigation.toggle")}
                        </span>
                      </SidebarMenuAction>
                    </CollapsibleTrigger>
                    <CollapsibleContent>
                      <SidebarMenuSub>
                        {/* Optional first child linking to original parent URL */}
                        {showPrimaryChild && (
                          <SidebarMenuSubItem key={`${item.title}__primary`}>
                            <SidebarMenuSubButton asChild>
                              <Link href={item.url}>
                                <span>{primaryChildLabel}</span>
                              </Link>
                            </SidebarMenuSubButton>
                          </SidebarMenuSubItem>
                        )}
                        {(item.items || []).map((subItem) => {
                          const hasSubChildren = !!subItem.items?.length;
                          const subItemKey = `${item.title}__${subItem.title}`;
                          const isSubOpen = openMap[subItemKey] ?? false;

                          return (
                            <SidebarMenuSubItem key={subItem.title}>
                              {hasSubChildren ? (
                                <Collapsible
                                  className="group/collapsible [&[data-state=open]>button>svg:first-child]:rotate-90"
                                  open={isSubOpen}
                                  onOpenChange={(next) =>
                                    setItemOpen(subItemKey, next)
                                  }
                                >
                                  <CollapsibleTrigger asChild>
                                    <SidebarMenuSubButton>
                                      <ChevronRight className="transition-transform group-data-[state=open]/collapsible:rotate-90" />
                                      {subItem.icon && <subItem.icon />}
                                      <span>{subItem.title}</span>
                                    </SidebarMenuSubButton>
                                  </CollapsibleTrigger>
                                  <CollapsibleContent>
                                    <SidebarMenuSub>
                                      {(subItem.items || []).map(
                                        (subSubItem) => (
                                          <SidebarMenuSubItem
                                            key={subSubItem.title}
                                          >
                                            <SidebarMenuSubButton asChild>
                                              <Link href={subSubItem.url}>
                                                <span>{subSubItem.title}</span>
                                              </Link>
                                            </SidebarMenuSubButton>
                                          </SidebarMenuSubItem>
                                        )
                                      )}
                                    </SidebarMenuSub>
                                  </CollapsibleContent>
                                </Collapsible>
                              ) : (
                                <SidebarMenuSubButton asChild>
                                  <Link href={subItem.url}>
                                    {subItem.icon && <subItem.icon />}
                                    <span>{subItem.title}</span>
                                  </Link>
                                </SidebarMenuSubButton>
                              )}
                            </SidebarMenuSubItem>
                          );
                        })}
                      </SidebarMenuSub>
                    </CollapsibleContent>
                  </>
                ) : (
                  <SidebarMenuButton asChild tooltip={item.title}>
                    <Link href={item.url}>
                      {item.icon && <item.icon />}
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                )}
              </SidebarMenuItem>
            </Collapsible>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
