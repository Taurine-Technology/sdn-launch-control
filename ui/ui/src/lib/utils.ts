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
