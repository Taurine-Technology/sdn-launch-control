/*
 * File: PortUtilizationSkeleton.tsx
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
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function PortUtilizationSkeleton() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <Skeleton className="h-6 w-48 bg-card" />
        </CardTitle>
        <CardDescription>
          <div className="space-y-2">
            <Skeleton className="h-4 w-full bg-card" />
            <div className="flex gap-4 flex-wrap">
              <Skeleton className="h-10 w-48 bg-card" />
              <Skeleton className="h-10 w-48 bg-card" />
              <Skeleton className="h-10 w-32 bg-card" />
            </div>
          </div>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Chart skeleton */}
          <div className="h-[400px] w-full relative">
            <Skeleton className="absolute inset-0 bg-card" />
          </div>
          {/* Legend skeleton */}
          <div className="flex gap-4 justify-center flex-wrap">
            <Skeleton className="h-4 w-24 bg-card" />
            <Skeleton className="h-4 w-24 bg-card" />
            <Skeleton className="h-4 w-24 bg-card" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
