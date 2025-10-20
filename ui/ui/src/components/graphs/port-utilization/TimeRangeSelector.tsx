/*
 * File: TimeRangeSelector.tsx
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

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useLanguage } from "@/context/languageContext";

interface TimeRangeSelectorProps {
  selectedHours: number;
  onHoursChange: (hours: number, interval: string) => void;
}

const timeRangeOptions = [
  { hours: 15 / 60, label: "15_minutes", interval: "10 seconds" }, // < 1 hour: 10 seconds
  { hours: 1, label: "1_hour", interval: "10 seconds" }, // < 1 hour: 10 seconds
  { hours: 6, label: "6_hours", interval: "1 minute" }, // 6 hours: 1 minute
  { hours: 24, label: "24_hours", interval: "5 minutes" }, // 24 hours: 5 minutes
  { hours: 168, label: "7_days", interval: "15 minutes" }, // 7 days: 15 minutes
];

/**
 * Determines the appropriate interval based on the time range
 * User requested:
 * - < 1 hour: 10 seconds (default)
 * - 6 hours: 1 minute
 * - > 6 hours: 5 minutes
 * - 24 hours: 10 minutes (using 5 minutes since 10 is not available)
 */
export function getIntervalForHours(hours: number): string {
  if (hours < 1) {
    return "10 seconds"; // Default for < 1 hour
  } else if (hours <= 6) {
    return "1 minute"; // 1-6 hours
  } else if (hours <= 24) {
    return "5 minutes"; // 6-24 hours
  } else {
    return "15 minutes"; // > 24 hours (e.g., 7 days)
  }
}

export function TimeRangeSelector({
  selectedHours,
  onHoursChange,
}: TimeRangeSelectorProps) {
  const { getT } = useLanguage();

  const handleChange = (value: string) => {
    const hours = parseFloat(value);
    const interval = getIntervalForHours(hours);
    onHoursChange(hours, interval);
  };

  return (
    <Select value={selectedHours.toString()} onValueChange={handleChange}>
      <SelectTrigger className="w-[180px]">
        <SelectValue
          placeholder={getT(
            "page.PortUtilizationPage.time_range",
            "Time Range"
          )}
        />
      </SelectTrigger>
      <SelectContent>
        {timeRangeOptions.map((option) => (
          <SelectItem key={option.hours} value={option.hours.toString()}>
            {getT(
              `page.PortUtilizationPage.time_ranges.${option.label}`,
              option.label.replace(/_/g, " ")
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
