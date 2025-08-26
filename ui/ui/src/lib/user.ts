/*
 * File: user.ts
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

import { createAxiosInstanceWithToken } from "./axiosInstance";
import type {
  UserData,
  UpdateUserProfileRequest,
  UpdateUserProfileResponse,
  ChangePasswordResponse,
  LinkTelegramRequest,
  LinkTelegramResponse,
  RefreshTokenResponse,
} from "./types";

export const getUserData = async (token: string): Promise<UserData> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const { data } = await axiosInstance.get("/account/profile/");
  console.log(data);
  return data;
};

export const updateUserProfile = async (
  token: string,
  user: Partial<UpdateUserProfileRequest>,
  profile: Partial<UpdateUserProfileRequest>
): Promise<UpdateUserProfileResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.put("/account/profile/", {
    ...user,
    ...profile,
  });
  return response.data;
};

export const updateUserPassword = async (
  token: string,
  oldPassword: string,
  newPassword: string
): Promise<ChangePasswordResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.post("/account/change-password/", {
    old_password: oldPassword,
    new_password: newPassword,
  });
  return response.data;
};

export const linkTelegram = async (
  token: string,
  payload: LinkTelegramRequest
): Promise<LinkTelegramResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.post(
    "/notifications/link-telegram/",
    payload
  );
  console.log(response);
  return response.data;
};

export const refreshToken = async (
  token: string
): Promise<RefreshTokenResponse> => {
  const axiosInstance = createAxiosInstanceWithToken(token);
  const response = await axiosInstance.post("/account/refresh-token/");
  return response.data;
};
