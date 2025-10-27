/*
 * File: authHelpers.ts
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

let logoutFunction: ((sessionExpired?: boolean) => void) | null = null;

/**
 * Sets the global logout function.
 * This should be called from your AuthProvider once the logout function is defined.
 *
 * @param fn - The logout function from AuthProvider.
 */
export const setLogoutFunction = (fn: (sessionExpired?: boolean) => void) => {
  logoutFunction = fn;
};

/**
 * Calls the global logout function if it exists.
 *
 * @param sessionExpired - Flag indicating if the logout is due to session expiration.
 */
export const logoutUser = (sessionExpired = false) => {
  if (logoutFunction) {
    logoutFunction(sessionExpired);
  } else {
    console.warn("Logout function is not set.");
  }
};
