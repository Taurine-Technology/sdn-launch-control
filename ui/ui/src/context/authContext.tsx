/*
 * File: authContext.ts
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
  useCallback,
} from "react";
import { useRouter } from "next/navigation";

import SessionExpiredDialog from "@/components/SessionExpiredDialog";
import { setLogoutFunction } from "@/lib/authHelpers";
import type { AuthContextType, AuthProviderProps } from "@/lib/types";
import { useNetwork } from "@/context/NetworkContext";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const [sessionExpired, setSessionExpired] = useState(false);
  const { resetNetworkData } = useNetwork();

  useEffect(() => {
    const loadTokens = async () => {
      try {
        const storedToken =
          typeof window !== "undefined"
            ? localStorage.getItem("taurineToken")
            : null;
        const storedUsername =
          typeof window !== "undefined"
            ? localStorage.getItem("taurineUsername")
            : null;
        if (storedToken) {
          setToken(storedToken);
          setIsAuthenticated(true);
          setUsername(storedUsername);
        } else {
          setIsAuthenticated(false);
          setUsername(null);
        }
      } catch {
        console.error("[AUTHCONTEXT] Error loading tokens");
        setIsAuthenticated(false);
        setUsername(null);
      } finally {
        setLoading(false);
      }
    };
    loadTokens();
  }, []);

  const authenticate = (token: string, username: string) => {
    setToken(token);
    setUsername(username);
    localStorage.setItem("taurineToken", token);
    localStorage.setItem("taurineUsername", username);
    setIsAuthenticated(true);
  };

  const logout = useCallback(
    (sessionExpiredFlag = false) => {
      console.log("[AUTHCONTEXT LOGOUT] resetting network data");
      resetNetworkData();

      localStorage.clear();
      setToken(null);
      setIsAuthenticated(false);
      setUsername(null);
      if (sessionExpiredFlag) {
        setSessionExpired(true);
      } else {
        router.push("/");
      }
    },
    [resetNetworkData, router]
  );

  useEffect(() => {
    setLogoutFunction(logout);
  }, [logout]);

  const handleDialogClose = () => {
    setSessionExpired(false);
    router.push("/");
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        authenticate,
        logout,
        loading,
        username,
        token,
      }}
    >
      {children}
      <SessionExpiredDialog
        open={sessionExpired}
        handleClose={handleDialogClose}
      />
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
