/*
 * File: ModelContext.tsx
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

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { ClassificationModel } from "@/lib/types";
import { fetchModelInfo, setActiveModel } from "@/lib/classifier";
import { toast } from "sonner";

interface ModelContextType {
  models: ClassificationModel[];
  activeModel: ClassificationModel | null;
  isLoading: boolean;
  error: string | null;
  refreshModels: () => Promise<void>;
  switchActiveModel: (modelName: string) => Promise<void>;
  getModelByName: (name: string) => ClassificationModel | undefined;
}

const ModelContext = createContext<ModelContextType | undefined>(undefined);

interface ModelProviderProps {
  children: ReactNode;
}

export const ModelProvider: React.FC<ModelProviderProps> = ({ children }) => {
  const [models, setModels] = useState<ClassificationModel[]>([]);
  const [activeModel, setActiveModelState] =
    useState<ClassificationModel | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadModels = async () => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchModelInfo(token);
      if (response.status === "success") {
        setModels(response.models);
        // Find the active model by name
        const activeModelObj = response.models.find(
          (model) => model.name === response.active_model
        );
        setActiveModelState(activeModelObj || null);
      } else {
        setError(response.message || "Failed to load models");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load models";
      setError(errorMessage);
      console.error("Error loading models:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshModels = async () => {
    await loadModels();
  };

  const switchActiveModel = async (modelName: string) => {
    const token = localStorage.getItem("taurineToken");
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await setActiveModel(token, modelName);
      if (response.status === "success") {
        // Refresh models to get updated state
        await loadModels();
        toast.success(`Switched to model: ${modelName}`);
      } else {
        setError(response.message || "Failed to switch model");
        toast.error(response.message || "Failed to switch model");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to switch model";
      setError(errorMessage);
      toast.error(errorMessage);
      console.error("Error switching model:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const getModelByName = (name: string): ClassificationModel | undefined => {
    return models.find((model) => model.name === name);
  };

  // Load models on mount
  useEffect(() => {
    loadModels();
  }, []);

  const value: ModelContextType = {
    models,
    activeModel,
    isLoading,
    error,
    refreshModels,
    switchActiveModel,
    getModelByName,
  };

  return (
    <ModelContext.Provider value={value}>{children}</ModelContext.Provider>
  );
};

export const useModel = (): ModelContextType => {
  const context = useContext(ModelContext);
  if (context === undefined) {
    throw new Error("useModel must be used within a ModelProvider");
  }
  return context;
};
