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
