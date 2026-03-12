import { createContext, useContext, useEffect, useState, useCallback } from "react";
import type { ReactNode } from "react";
import { theme as antTheme } from "antd";
import { request } from "../api/request";

interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

interface ThemeState {
  mode: "light" | "dark" | "system";
  colorThemeId: string;
  colors: ThemeColors | null;
  isDark: boolean;
}

interface ThemeContextValue extends ThemeState {
  setMode: (mode: "light" | "dark" | "system") => void;
  setColorTheme: (themeId: string, colors: ThemeColors) => void;
  antAlgorithm: typeof antTheme.defaultAlgorithm;
  antTokenOverrides: Record<string, string>;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveIsDark(mode: "light" | "dark" | "system"): boolean {
  if (mode === "dark") return true;
  if (mode === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<ThemeState>({
    // Default to light for a more welcoming first-run experience.
    mode: (localStorage.getItem("prowlrbot-theme-mode") as ThemeState["mode"]) || "light",
    colorThemeId: localStorage.getItem("prowlrbot-color-theme") || "tech-innovation",
    colors: null,
    isDark: resolveIsDark(
      (localStorage.getItem("prowlrbot-theme-mode") as ThemeState["mode"]) || "light",
    ),
  });

  // Load saved settings from backend on mount
  useEffect(() => {
    request<{ theme: string; color_theme: string }>("/settings/all")
      .then((data) => {
        if (data) {
          const mode = (data.theme || "system") as ThemeState["mode"];
          const colorThemeId = data.color_theme || "tech-innovation";
          localStorage.setItem("prowlrbot-theme-mode", mode);
          localStorage.setItem("prowlrbot-color-theme", colorThemeId);
          setState((prev) => ({
            ...prev,
            mode,
            colorThemeId,
            isDark: resolveIsDark(mode),
          }));
        }
      })
      .catch(() => {});

    // Load color theme details
    request<{ themes: Array<{ id: string; colors: ThemeColors }>; active: string }>(
      "/settings/themes",
    )
      .then((data) => {
        if (data?.themes) {
          const active = data.themes.find((t) => t.id === data.active);
          if (active) {
            setState((prev) => ({ ...prev, colors: active.colors }));
          }
        }
      })
      .catch(() => {});
  }, []);

  // Listen to system preference changes
  useEffect(() => {
    if (state.mode !== "system") return;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => {
      setState((prev) => ({ ...prev, isDark: e.matches }));
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [state.mode]);

  // Apply CSS class for dark mode
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", state.isDark ? "dark" : "light");
  }, [state.isDark]);

  // Apply CSS variables for color theme
  useEffect(() => {
    if (!state.colors) return;
    const root = document.documentElement;
    root.style.setProperty("--prowlrbot-primary", state.colors.primary);
    root.style.setProperty("--prowlrbot-secondary", state.colors.secondary);
    root.style.setProperty("--prowlrbot-accent", state.colors.accent);
    root.style.setProperty("--prowlrbot-background", state.colors.background);
  }, [state.colors]);

  const setMode = useCallback((mode: "light" | "dark" | "system") => {
    localStorage.setItem("prowlrbot-theme-mode", mode);
    setState((prev) => ({ ...prev, mode, isDark: resolveIsDark(mode) }));
  }, []);

  const setColorTheme = useCallback((themeId: string, colors: ThemeColors) => {
    localStorage.setItem("prowlrbot-color-theme", themeId);
    setState((prev) => ({ ...prev, colorThemeId: themeId, colors }));
  }, []);

  const antAlgorithm = state.isDark ? antTheme.darkAlgorithm : antTheme.defaultAlgorithm;

  const antTokenOverrides: Record<string, string> = {};
  if (state.colors) {
    antTokenOverrides.colorPrimary = state.colors.primary;
  }

  return (
    <ThemeContext.Provider
      value={{
        ...state,
        setMode,
        setColorTheme,
        antAlgorithm,
        antTokenOverrides,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
