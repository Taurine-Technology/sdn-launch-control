/*
 * File: classifier.ts
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

import { createAxiosInstanceWithToken } from "./axiosInstance";
import {
  CategoryApiResponse,
  ModelInfoApiResponse,
  SetActiveModelRequest,
  SetActiveModelResponse,
} from "./types";

/**
 * Fetches categories from the backend.
 */
export const fetchCategories = async (
  token: string,
  modelName?: string,
  includeLegacy?: boolean
): Promise<CategoryApiResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);

  const params = new URLSearchParams();
  if (modelName) {
    params.append("model_name", modelName);
  }
  if (includeLegacy) {
    params.append("include_legacy", "true");
  }

  const url = params.toString()
    ? `/categories/?${params.toString()}`
    : "/categories/";
  const { data } = await axiosInstance.get<CategoryApiResponse>(url);
  console.log(data);
  return data;
};

/**
 * Fetches model information from the backend.
 */
export const fetchModelInfo = async (
  token: string
): Promise<ModelInfoApiResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get<ModelInfoApiResponse>(
    "/models/info/"
  );
  return data;
};

/**
 * Sets the active classification model.
 */
export const setActiveModel = async (
  token: string,
  modelName: string
): Promise<SetActiveModelResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const payload: SetActiveModelRequest = { model_name: modelName };
  const { data } = await axiosInstance.post<SetActiveModelResponse>(
    "/models/",
    payload
  );
  return data;
};

/**
 * Fetches classification statistics from the backend.
 */
export const getClassificationStats = async (
  token: string,
  params: {
    model_name?: string;
    hours?: number;
    summary?: boolean;
  } = {}
): Promise<{
  data: {
    summary?: {
      confidence_breakdown: {
        high_confidence: { count: number; percentage: number };
        low_confidence: { count: number; percentage: number };
        multiple_candidates: { count: number; percentage: number };
        uncertain: { count: number; percentage: number };
      };
      total_classifications: number;
      avg_prediction_time_ms: number;
    };
    periods?: Array<{
      high_confidence_count: number;
      low_confidence_count: number;
      multiple_candidates_count: number;
      uncertain_count: number;
      total_classifications: number;
      avg_prediction_time_ms: number;
    }>;
  };
}> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  
  const queryParams = new URLSearchParams();
  if (params.model_name) {
    queryParams.append("model_name", params.model_name);
  }
  if (params.hours) {
    queryParams.append("hours", params.hours.toString());
  }
  if (params.summary !== undefined) {
    queryParams.append("summary", params.summary.toString());
  }

  const url = queryParams.toString()
    ? `/classification-stats/?${queryParams.toString()}`
    : "/classification-stats/";
    
  const { data } = await axiosInstance.get(url);
  return data;
};
