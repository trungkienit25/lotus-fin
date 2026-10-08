import React, { createContext, useContext, useState, useMemo } from "react";
import { Language, TranslationDictionary } from "./types";
import { en } from "./locales/en";
import { vi } from "./locales/vi";
import { zh } from "./locales/zh";

const translations: Record<Language, TranslationDictionary> = { en, vi, zh };

export interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (path: string, params?: Record<string, string | number>) => string;
  languages: { code: Language; label: string; flag: string }[];
}

const I18nContext = createContext<I18nContextType | null>(null);

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>("en");

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("lotus_language", lang);
    document.documentElement.lang = lang;
  };

  const t = useMemo(() => {
    const dict = translations[language] || translations.en;

    return (path: string, params?: Record<string, string | number>): string => {
      const keys = path.split(".");
      let current: any = dict;

      for (const key of keys) {
        if (current && typeof current === "object" && key in current) {
          current = current[key];
        } else {
          // Fallback to English dictionary
          let fallback: any = translations.en;
          for (const fKey of keys) {
            if (fallback && typeof fallback === "object" && fKey in fallback) {
              fallback = fallback[fKey];
            } else {
              return path;
            }
          }
          current = fallback;
          break;
        }
      }

      if (typeof current !== "string") {
        return path;
      }

      if (params) {
        return Object.entries(params).reduce((str, [paramKey, paramVal]) => {
          return str.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramVal));
        }, current);
      }

      return current;
    };
  }, [language]);

  const languages = useMemo(
    () => [
      { code: "en" as Language, label: "English", flag: "US" },
      { code: "vi" as Language, label: "Tiếng Việt", flag: "VN" },
      { code: "zh" as Language, label: "中文 (Chinese)", flag: "CN" },
    ],
    []
  );

  return (
    <I18nContext.Provider value={{ language, setLanguage, t, languages }}>
      {children}
    </I18nContext.Provider>
  );
};

export const useTranslation = (): I18nContextType => {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Return safe English fallback if used outside provider
    const tFallback = (path: string, params?: Record<string, string | number>): string => {
      const keys = path.split(".");
      let current: any = en;
      for (const key of keys) {
        if (current && typeof current === "object" && key in current) {
          current = current[key];
        } else {
          return path;
        }
      }
      if (typeof current !== "string") return path;
      if (params) {
        return Object.entries(params).reduce((str, [paramKey, paramVal]) => {
          return str.replace(new RegExp(`\\{${paramKey}\\}`, "g"), String(paramVal));
        }, current);
      }
      return current;
    };

    return {
      language: "en",
      setLanguage: () => {},
      t: tFallback,
      languages: [
        { code: "en", label: "English", flag: "US" },
        { code: "vi", label: "Tiếng Việt", flag: "VN" },
        { code: "zh", label: "中文 (Chinese)", flag: "CN" },
      ],
    };
  }
  return ctx;
};

