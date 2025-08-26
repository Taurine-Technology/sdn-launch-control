/*
 * File: ModelSelectionComponent.tsx
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

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useModel } from "@/context/ModelContext";
import { useLanguage } from "@/context/languageContext";
import { ClassificationModel } from "@/lib/types";

interface ModelSelectionComponentProps {
  selectedModel?: string;
  onModelChange?: (modelName: string) => void;
  showActiveIndicator?: boolean;
  showModelDetails?: boolean;
  disabled?: boolean;
  className?: string;
}

export const ModelSelectionComponent: React.FC<
  ModelSelectionComponentProps
> = ({
  selectedModel,
  onModelChange,
  showActiveIndicator = true,
  showModelDetails = true,
  disabled = false,
  className = "",
}) => {
  const { getT } = useLanguage();
  const { models, activeModel, isLoading, switchActiveModel } = useModel();

  const handleModelChange = async (modelName: string) => {
    if (onModelChange) {
      onModelChange(modelName);
    } else {
      // Default behavior: switch active model
      await switchActiveModel(modelName);
    }
  };

  const getModelStatusBadge = (model: ClassificationModel) => {
    if (model.is_active) {
      return (
        <Badge variant="default" className="ml-2">
          {getT("components.meters.active", "Active")}
        </Badge>
      );
    }
    if (model.is_loaded) {
      return (
        <Badge variant="secondary" className="ml-2">
          {getT("components.meters.loaded", "Loaded")}
        </Badge>
      );
    }
    return (
      <Badge variant="outline" className="ml-2">
        {getT("components.meters.inactive", "Inactive")}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>
            <Skeleton className="h-6 w-32" />
          </CardTitle>
          <CardDescription>
            <Skeleton className="h-4 w-48" />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-full" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>
          {getT(
            "components.meters.classification_model",
            "Classification Model"
          )}
        </CardTitle>
        <CardDescription>
          {getT(
            "components.meters.select_model_description",
            "Choose a classification model to use for traffic analysis"
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Select
          value={selectedModel || activeModel?.name || ""}
          onValueChange={handleModelChange}
          disabled={disabled}
        >
          <SelectTrigger>
            <SelectValue
              placeholder={getT(
                "components.meters.select_model_placeholder",
                "Select a model"
              )}
            />
          </SelectTrigger>
          <SelectContent>
            {models.map((model) => (
              <SelectItem key={model.name} value={model.name}>
                <div className="flex items-center justify-between w-full">
                  <span>{model.name}</span>
                  {showActiveIndicator && getModelStatusBadge(model)}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {showModelDetails && activeModel && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {getT("components.meters.version", "Version")}:
              </span>
              <span className="text-sm text-muted-foreground">
                {activeModel.version}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {getT("components.meters.categories", "Categories")}:
              </span>
              <span className="text-sm text-muted-foreground">
                {activeModel.num_categories}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {getT("components.meters.model_type", "Model Type")}:
              </span>
              <span className="text-sm text-muted-foreground">
                {activeModel.model_type}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {getT(
                  "components.meters.confidence_threshold",
                  "Confidence Threshold"
                )}
                :
              </span>
              <span className="text-sm text-muted-foreground">
                {(activeModel.confidence_threshold * 100).toFixed(0)}%
              </span>
            </div>
            {activeModel.description && (
              <div className="space-y-1">
                <span className="text-sm font-medium">
                  {getT("components.meters.description", "Description")}:
                </span>
                <p className="text-sm text-muted-foreground line-clamp-3 leading-relaxed">
                  {activeModel.description}
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
