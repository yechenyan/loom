import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export const locales = ["en", "de", "zh"] as const;
export type Locale = (typeof locales)[number];

const STORAGE_KEY = "loom-web-locale";

const localeNames: Record<Locale, string> = {
  en: "English",
  de: "Deutsch",
  zh: "中文",
};

type I18nContextValue = {
  locale: Locale;
  localeNames: Record<Locale, string>;
  setLocale: (locale: Locale) => void;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => readStoredLocale());

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, locale);
    document.documentElement.lang = locale;
  }, [locale]);

  return (
    <I18nContext.Provider value={{ locale, localeNames, setLocale }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) {
    throw new Error("useI18n must be used inside I18nProvider");
  }

  return value;
}

function readStoredLocale(): Locale {
  if (typeof window === "undefined") {
    return "en";
  }

  const value = localStorage.getItem(STORAGE_KEY);
  return isLocale(value) ? value : "en";
}

function isLocale(value: string | null): value is Locale {
  return value === "en" || value === "de" || value === "zh";
}
