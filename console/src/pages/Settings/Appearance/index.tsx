import { useState, useEffect, useCallback } from "react";
import { Button, message } from "antd";
import { CheckCircleFilled } from "@ant-design/icons";
import { request } from "../../../api";
import { useTheme } from "../../../contexts/ThemeContext";
import styles from "./index.module.less";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

interface ThemeFonts {
  header: string;
  body: string;
}

interface Theme {
  id: string;
  name: string;
  description: string;
  best_for: string;
  colors: ThemeColors;
  fonts: ThemeFonts;
}

/* ------------------------------------------------------------------ */
/* Main Page                                                           */
/* ------------------------------------------------------------------ */

function AppearancePage() {
  const { setMode: applyMode, setColorTheme: applyColorTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [activeTheme, setActiveTheme] = useState<string>("tech-innovation");
  const [mode, setMode] = useState<string>("system");

  const fetchThemes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await request<{ themes: Theme[]; active: string }>(
        "/settings/themes",
      ).catch(() => null);
      if (data && data.themes) {
        setThemes(data.themes);
        setActiveTheme(data.active);
      }

      // Also fetch current mode (light/dark/system)
      const allSettings = await request<{ theme: string }>(
        "/settings/all",
      ).catch(() => null);
      if (allSettings?.theme) {
        setMode(allSettings.theme);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load theme settings",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchThemes();
  }, [fetchThemes]);

  /* ---- Select color theme ---- */

  const handleSelectTheme = async (themeId: string) => {
    const prev = activeTheme;
    setActiveTheme(themeId);
    const selectedTheme = themes.find((t) => t.id === themeId);
    if (selectedTheme) {
      applyColorTheme(themeId, selectedTheme.colors);
    }
    try {
      await request("/settings/color-theme", {
        method: "PUT",
        body: JSON.stringify({ color_theme: themeId }),
      });
      message.success(
        `Theme set to ${selectedTheme?.name}`,
      );
    } catch {
      setActiveTheme(prev);
      if (prev) {
        const prevTheme = themes.find((t) => t.id === prev);
        if (prevTheme) applyColorTheme(prev, prevTheme.colors);
      }
      message.error("Failed to save theme selection");
    }
  };

  /* ---- Select mode ---- */

  const handleSelectMode = async (newMode: string) => {
    const prev = mode;
    setMode(newMode);
    applyMode(newMode as "light" | "dark" | "system");
    try {
      await request("/settings/theme", {
        method: "PUT",
        body: JSON.stringify({ theme: newMode }),
      });
      message.success(`Display mode set to ${newMode}`);
    } catch {
      setMode(prev);
      applyMode(prev as "light" | "dark" | "system");
      message.error("Failed to save display mode");
    }
  };

  /* ---- render ---- */

  return (
    <div className={styles.page}>
      {/* ---- Page header ---- */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Appearance</h2>
        <p className={styles.sectionDesc}>
          Customize how ProwlrBot looks. Choose a color theme and display mode.
        </p>
      </div>

      {loading ? (
        <div className={styles.centerState}>
          <span className={styles.stateText}>Loading themes...</span>
        </div>
      ) : error ? (
        <div className={styles.centerState}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🎨</div>
          <span className={styles.stateTextError}>Could not load theme settings</span>
          <span className={styles.stateText} style={{ marginTop: 4, maxWidth: 400, textAlign: "center", lineHeight: 1.5 }}>
            Make sure the ProwlrBot server is running with &apos;prowlr app&apos;.
          </span>
          <details style={{ marginTop: 8, fontSize: 11, color: "var(--pb-text-disabled)" }}>
            <summary style={{ cursor: "pointer" }}>Technical details</summary>
            <code style={{ display: "block", marginTop: 4, padding: 8, background: "var(--pb-bg-code)", borderRadius: 4 }}>{error}</code>
          </details>
          <Button
            size="small"
            onClick={fetchThemes}
            style={{ marginTop: 12 }}
          >
            Retry
          </Button>
        </div>
      ) : (
        <>
          {/* ---- Display Mode ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Display Mode</div>
            <div className={styles.modeGrid}>
              {[
                { id: "light", label: "Light", icon: "\u2600\uFE0F" },
                { id: "dark", label: "Dark", icon: "\uD83C\uDF19" },
                { id: "system", label: "System", icon: "\uD83D\uDCBB" },
              ].map((m) => (
                <div
                  key={m.id}
                  className={`${styles.modeCard} ${mode === m.id ? styles.modeCardActive : ""}`}
                  onClick={() => handleSelectMode(m.id)}
                >
                  <div className={styles.modeIcon}>{m.icon}</div>
                  <div className={styles.modeLabel}>{m.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ---- Color Themes ---- */}
          <div className={styles.cardSection}>
            <div className={styles.cardSectionTitle}>Color Theme</div>
            <div className={styles.themeGrid}>
              {themes.map((theme) => {
                const isActive = theme.id === activeTheme;
                return (
                  <div
                    key={theme.id}
                    className={`${styles.themeCard} ${isActive ? styles.themeCardActive : ""}`}
                    onClick={() => handleSelectTheme(theme.id)}
                  >
                    {/* Color swatches */}
                    <div className={styles.themeSwatches}>
                      <div
                        className={styles.themeSwatch}
                        style={{ backgroundColor: theme.colors.primary }}
                      />
                      <div
                        className={styles.themeSwatch}
                        style={{ backgroundColor: theme.colors.secondary }}
                      />
                      <div
                        className={styles.themeSwatch}
                        style={{ backgroundColor: theme.colors.accent }}
                      />
                      <div
                        className={styles.themeSwatch}
                        style={{ backgroundColor: theme.colors.background }}
                      />
                    </div>

                    {/* Info */}
                    <div className={styles.themeName}>{theme.name}</div>
                    <div className={styles.themeDescription}>
                      {theme.description}
                    </div>
                    <div className={styles.themeBestFor}>{theme.best_for}</div>

                    {/* Active indicator */}
                    {isActive && (
                      <div className={styles.activeLabel}>
                        <CheckCircleFilled /> Active
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default AppearancePage;
