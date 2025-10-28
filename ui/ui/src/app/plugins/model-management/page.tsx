/*
 * File: page.tsx
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

import React, { useEffect } from "react";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
} from "@/components/ui/breadcrumb";
import ProtectedRoute from "@/lib/ProtectedRoute";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useModel } from "@/context/ModelContext";
import { useLanguage } from "@/context/languageContext";
import { ClassificationModel } from "@/lib/types";
import {
  Activity,
  Database,
  Play,
  Settings,
  TrendingUp,
  Users,
} from "lucide-react";

export default function ModelManagementPage() {
  const { getT } = useLanguage();
  const {
    models,
    activeModel,
    isLoading,
    error,
    switchActiveModel,
    refreshModels,
  } = useModel();

  const handleSwitchModel = async (model: ClassificationModel) => {
    if (model.is_active) return;
    await switchActiveModel(model.name);
  };

  const getModelStatusBadge = (model: ClassificationModel) => {
    if (model.is_active) {
      return (
        <Badge variant="default" className="bg-green-600">
          <Activity className="w-3 h-3 mr-1" />
          {getT("components.meters.active", "Active")}
        </Badge>
      );
    }
    if (model.is_loaded) {
      return (
        <Badge variant="secondary">
          <Database className="w-3 h-3 mr-1" />
          {getT("components.meters.loaded", "Loaded")}
        </Badge>
      );
    }
    return (
      <Badge variant="outline">
        <Settings className="w-3 h-3 mr-1" />
        {getT("components.meters.inactive", "Inactive")}
      </Badge>
    );
  };

  // Refresh to ensure model list is up-to-date when navigating to page (on first set up this can be an issue)
  useEffect(() => {
    refreshModels();
  }, [refreshModels]);

  if (isLoading) {
    return (
      <ProtectedRoute>
        <SidebarProvider
          style={
            {
              "--sidebar-width": "calc(var(--spacing) * 72)",
              "--header-height": "calc(var(--spacing) * 12)",
            } as React.CSSProperties
          }
        >
          <AppSidebar />
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center gap-2">
              <div className="flex items-center gap-2 px-4">
                <SidebarTrigger className="-ml-1" />
                <Separator
                  orientation="vertical"
                  className="mr-2 data-[orientation=vertical]:h-4"
                />
                <Breadcrumb>
                  <BreadcrumbList>
                    <BreadcrumbItem className="hidden md:block">
                      <BreadcrumbLink href="/plugins">
                        {getT("navigation.plugins", "Plugins")}
                      </BreadcrumbLink>
                    </BreadcrumbItem>
                  </BreadcrumbList>
                </Breadcrumb>
              </div>
            </header>

            <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
              <div className="space-y-4">
                <Skeleton className="h-8 w-[300px]" />
                <Skeleton className="h-4 w-[500px]" />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <Card key={i}>
                    <CardHeader>
                      <Skeleton className="h-6 w-32" />
                      <Skeleton className="h-4 w-48" />
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-8 w-24" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <SidebarProvider
        style={
          {
            "--sidebar-width": "calc(var(--spacing) * 72)",
            "--header-height": "calc(var(--spacing) * 12)",
          } as React.CSSProperties
        }
      >
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-2">
            <div className="flex items-center gap-2 px-4">
              <SidebarTrigger className="-ml-1" />
              <Separator
                orientation="vertical"
                className="mr-2 data-[orientation=vertical]:h-4"
              />
              <Breadcrumb>
                <BreadcrumbList>
                  <BreadcrumbItem className="hidden md:block">
                    <BreadcrumbLink href="/plugins">
                      {getT("navigation.plugins", "Plugins")}
                    </BreadcrumbLink>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
          </header>

          <div className="@container/main w-full flex flex-col gap-6 px-4 lg:px-8 py-8">
            <div className="w-full flex flex-row items-end justify-between mb-6">
              <div>
                <h1 className="text-2xl font-bold text-muted-foreground">
                  {getT("page.ModelManagement.page_title", "Model Management")}
                </h1>
                <p className="text-muted-foreground mt-2">
                  {getT(
                    "page.ModelManagement.page_description",
                    "Manage and monitor classification models for traffic analysis"
                  )}
                </p>
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Active Model Overview */}
            {activeModel && (
              <Card className="border-green-500 border-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-green-600" />
                    {getT("page.ModelManagement.active_model", "Active Model")}
                  </CardTitle>
                  <CardDescription>
                    {getT(
                      "page.ModelManagement.active_model_description",
                      "Currently active classification model"
                    )}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        {getT("components.meters.name", "Name")}
                      </p>
                      <p className="text-lg font-semibold">
                        {activeModel.name}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        {getT("components.meters.version", "Version")}
                      </p>
                      <p className="text-lg font-semibold">
                        {activeModel.version}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        {getT("components.meters.categories", "Categories")}
                      </p>
                      <p className="text-lg font-semibold">
                        {activeModel.num_categories}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        {getT("components.meters.status", "Status")}
                      </p>
                      <div className="mt-1">
                        {getModelStatusBadge(activeModel)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Models Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {models.map((model) => (
                <Card
                  key={model.name}
                  className={model.is_active ? "border-green-500 border-2" : ""}
                >
                  <CardHeader className="relative">
                    <div>
                      <CardTitle className="text-lg">{model.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {model.description ||
                          getT(
                            "components.meters.no_description",
                            "No description available"
                          )}
                      </CardDescription>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">
                          {getT("components.meters.version", "Version")}
                        </p>
                        <p className="font-medium">{model.version}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">
                          {getT("components.meters.categories", "Categories")}
                        </p>
                        <p className="font-medium">{model.num_categories}</p>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">
                        {getT(
                          "components.meters.model_info",
                          "Model Information"
                        )}
                      </p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between">
                          <span>Type:</span>
                          <span className="font-medium">
                            {model.model_type}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Confidence:</span>
                          <span className="font-medium">
                            {(model.confidence_threshold * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Meters:</span>
                          <span className="font-medium">
                            {model.meter_count}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>File:</span>
                          <span className="font-medium">
                            {model.file_exists ? "Exists" : "Missing"}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Users className="w-3 h-3" />
                        {model.num_categories} categories
                      </div>
                      <div className="flex items-center gap-1">
                        <Database className="w-3 h-3" />
                        {model.meter_count} meters
                      </div>
                    </div>

                    {!model.is_active && (
                      <Button
                        onClick={() => handleSwitchModel(model)}
                        className="w-full"
                        size="sm"
                      >
                        <Play className="w-4 h-4 mr-2" />
                        {getT("components.meters.activate", "Activate")}
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            {models.length === 0 && !isLoading && (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <TrendingUp className="w-12 h-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    {getT("page.ModelManagement.no_models", "No Models Found")}
                  </h3>
                  <p className="text-muted-foreground text-center">
                    {getT(
                      "page.ModelManagement.no_models_description",
                      "No classification models are currently available. Models will appear here once they are installed and configured."
                    )}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  );
}
