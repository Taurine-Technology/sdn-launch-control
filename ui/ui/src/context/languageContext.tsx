/*
 * File: languageContext.tsx
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
 *
 * NOTE: When adding a new language, update the Language type, import the translation file,
 * and add it to the setLanguage and useEffect logic below.
 */
"use client";
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import en from "@/locales/en.json";
import es from "@/locales/es.json";
import { Translations, getTranslation } from "@/lib/types";

export type Language = "en" | "es";

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
  getT: (path: string, fallback?: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(
  undefined
);

// If you add more languages, import them here and update the Language type.
const enTranslations: typeof en = en;
const esTranslations: typeof es = es;

export const LanguageProvider = ({ children }: { children: ReactNode }) => {
  const [language, setLanguageState] = useState<Language>("en");
  const [t, setT] = useState<Translations>(en);

  useEffect(() => {
    const storedLang =
      typeof window !== "undefined" ? localStorage.getItem("language") : null;
    if (storedLang === "es") {
      setLanguageState("es");
      setT(esTranslations);
    } else {
      setLanguageState("en");
      setT(enTranslations);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("language", lang);
    setT(lang === "es" ? esTranslations : enTranslations);
  };

  const getT = (path: string, fallback: string = "") => {
    return getTranslation(t, path, fallback);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, getT }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
};
