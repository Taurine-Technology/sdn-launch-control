/*
 * File: utils.ts
 * Copyright (C) 2025 Taurine Technology
 *
 * This file is part of the SDN Launch Control project.
 *
 * This project is licensed under the GNU General Public License v3.0 (GPL-3.0),
 * available at: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
 *
 * Contributions to this project are governed by a Contributor License Agreement (CLA).
 * By submitting a contribution, contributors grant Taurine Technology exclusive rights to
 * the contribution, including the right to relicense it under a different license
 * at the copyright owner's discretion.
 *
 * Unless required by applicable law or agreed to in writing, software distributed
 * under this license is provided "AS IS", WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the GNU General Public License for more details.
 *
 * For inquiries, contact Keegan White at keeganwhite@taurinetech.com.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function stripTrailingSlash(url: string): string {
  return url.replace(/\/+$/, "");
}

export function validateApiUrl(url: string): string {
  if (!url.trim()) {
    return "";
  }
  try {
    const newUrl = new URL(url);
    if (newUrl.protocol !== "http:" && newUrl.protocol !== "https:") {
      return "API URL must start with http:// or https://";
    }
  } catch (error) {
    console.error("[UTILS] Invalid API URL format.", error);
    return "Invalid API URL format.";
  }
  return ""; // No error
}
