/*
 * File: chartColors.ts
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

/**
 * Centralized color palette for all charts in the application.
 * Colors are chosen to be visually distinct and avoid confusion with status indicators.
 *
 * Note: Red is avoided as it typically indicates errors/warnings in UIs.
 *
 * With 20 colors, this palette can handle up to 20 simultaneous lines/series
 * before colors start repeating.
 */
export const CHART_COLORS = [
  "#2563eb", // Blue - Primary
  "#16a34a", // Green - Success/positive
  "#9333ea", // Purple - Distinct
  "#ea580c", // Orange - Warm
  "#0891b2", // Cyan - Cool
  "#7c3aed", // Violet - Deep
  "#059669", // Emerald - Fresh
  "#0284c7", // Sky Blue - Light
  "#6366f1", // Indigo - Rich
  "#8b5cf6", // Purple variant
  "#14b8a6", // Teal - Aqua
  "#0ea5e9", // Light Blue
  "#10b981", // Green variant
  "#3b82f6", // Blue variant
  "#a855f7", // Purple light
  "#06b6d4", // Cyan bright
  "#84cc16", // Lime - Fresh green
  "#f59e0b", // Amber - Golden
  "#6366f1", // Indigo variant
  "#8b5cf6", // Violet variant
] as const;

/**
 * Status colors for indicators (warnings, peaks, etc.)
 */
export const STATUS_COLORS = {
  warning: "#eab308", // Yellow - For warnings/peaks
  success: "#16a34a", // Green - For success states
  info: "#0891b2", // Cyan - For informational
  error: "#dc2626", // Red - For errors only (use sparingly)
} as const;

/**
 * Get a chart color by index.
 * Automatically wraps around if index exceeds available colors.
 *
 * @param index - The index of the color to retrieve
 * @returns A hex color string
 */
export function getChartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length];
}

/**
 * Generate an array of chart colors for a given count.
 *
 * @param count - Number of colors needed
 * @returns Array of hex color strings
 */
export function generateChartColors(count: number): string[] {
  return Array.from({ length: count }, (_, i) => getChartColor(i));
}

/**
 * Get a color for a specific key (e.g., device IP, port name).
 * Uses a simple hash to ensure consistent colors for the same key.
 *
 * @param key - String key to generate color for
 * @returns A hex color string
 */
export function getColorForKey(key: string): string {
  // Simple hash function
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = key.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % CHART_COLORS.length;
  return CHART_COLORS[index];
}
