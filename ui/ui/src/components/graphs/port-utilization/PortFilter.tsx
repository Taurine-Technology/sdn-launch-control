/*
 * File: PortFilter.tsx
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

import { useState } from "react";
import { Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { useLanguage } from "@/context/languageContext";
import { cn } from "@/lib/utils";

interface PortFilterProps {
  ports: string[];
  selectedPorts: string[];
  onChange: (ports: string[]) => void;
}

/**
 * PortFilter component for selecting ports to display.
 *
 * @param ports - Array of available port names
 * @param selectedPorts - Array of selected port names.
 *                        Empty array ([]) means "all ports selected".
 *                        Non-empty array means specific ports are selected.
 * @param onChange - Callback when port selection changes
 */
export function PortFilter({
  ports,
  selectedPorts,
  onChange,
}: PortFilterProps) {
  const { getT } = useLanguage();
  const [open, setOpen] = useState(false);

  const isAllSelected =
    selectedPorts.length === 0 || selectedPorts.length === ports.length;

  const getDisplayText = () => {
    if (isAllSelected) {
      return getT("page.PortUtilizationPage.all_ports", "All Ports");
    }
    if (selectedPorts.length === 1) {
      return selectedPorts[0];
    }
    const template = getT(
      "page.PortUtilizationPage.ports_selected",
      "{count} ports selected"
    );
    return template.replace("{count}", selectedPorts.length.toString());
  };

  const handleSelectAll = () => {
    onChange([]);
  };

  const handleTogglePort = (port: string) => {
    const newSelectedPorts = selectedPorts.includes(port)
      ? selectedPorts.filter((p) => p !== port)
      : [...selectedPorts, port];

    // If all ports are selected, set to empty array (means "all")
    if (newSelectedPorts.length === ports.length) {
      onChange([]);
    } else {
      onChange(newSelectedPorts);
    }
  };

  const isPortSelected = (port: string) => {
    return isAllSelected || selectedPorts.includes(port);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[250px] justify-between"
        >
          <span className="truncate">{getDisplayText()}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[250px] p-0">
        <div className="max-h-[300px] overflow-y-auto">
          <div className="p-2">
            {/* Select All option */}
            <div
              className={cn(
                "flex items-center space-x-2 rounded-sm px-2 py-1.5 cursor-pointer hover:bg-accent",
                isAllSelected && "bg-accent"
              )}
              onClick={(e) => {
                // Only trigger if clicking the container, not the checkbox
                if (e.target === e.currentTarget) {
                  handleSelectAll();
                }
              }}
            >
              <Checkbox
                checked={isAllSelected}
                onCheckedChange={handleSelectAll}
              />
              <span className="flex-1 text-sm font-medium">
                {getT("page.PortUtilizationPage.all_ports", "All Ports")}
              </span>
              {isAllSelected && <Check className="h-4 w-4" />}
            </div>

            {/* Individual port options */}
            <div className="mt-2 border-t pt-2">
              {ports.map((port) => (
                <div
                  key={port}
                  className={cn(
                    "flex items-center space-x-2 rounded-sm px-2 py-1.5 cursor-pointer hover:bg-accent",
                    isPortSelected(port) && "bg-accent"
                  )}
                  onClick={(e) => {
                    // Only trigger if clicking the container, not the checkbox
                    if (e.target === e.currentTarget) {
                      handleTogglePort(port);
                    }
                  }}
                >
                  <Checkbox
                    checked={isPortSelected(port)}
                    onCheckedChange={() => handleTogglePort(port)}
                  />
                  <span className="flex-1 text-sm truncate">{port}</span>
                  {isPortSelected(port) && <Check className="h-4 w-4" />}
                </div>
              ))}
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
