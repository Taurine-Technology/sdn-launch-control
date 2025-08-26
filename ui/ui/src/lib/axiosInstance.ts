/*
 * File: axiosInstance.ts
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
import axios, { AxiosInstance, AxiosResponse, AxiosError } from "axios";
import { logoutUser } from "./authHelpers";
import { stripTrailingSlash } from "./utils";

export const createAxiosInstanceWithToken = (token: string): AxiosInstance => {
  const baseURL = stripTrailingSlash(
    process.env.NEXT_PUBLIC_API_BASE_URL || ""
  );
  const instance = axios.create({
    baseURL,
    headers: {
      Authorization: `Token ${token}`,
    },
  });

  instance.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error: AxiosError) => {
      if (error.response && error.response.status === 401) {
        logoutUser(true);
      }
      return Promise.reject(error);
    }
  );

  return instance;
};

export const createAxiosInstance = (): AxiosInstance => {
  const baseURL = stripTrailingSlash(
    process.env.NEXT_PUBLIC_API_BASE_URL || ""
  );
  return axios.create({
    baseURL,
  });
};
