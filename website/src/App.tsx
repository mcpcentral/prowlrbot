import { useEffect, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { loadSiteConfig, type SiteConfig } from "./config";
import { type Lang, t } from "./i18n";
import { Home } from "./pages/Home";
import { Docs } from "./pages/Docs";
import { Blog } from "./pages/Blog";
import { Marketplace } from "./pages/Marketplace";
import { Pricing } from "./pages/Pricing";
import { AgentGreeting } from "./components/AgentGreeting";
import "./index.css";

const LANG_KEY = "site-lang";
const THEME_KEY = "site-theme";

function getStoredLang(): Lang {
  const v = localStorage.getItem(LANG_KEY);
  return v === "zh" ? "zh" : "en";
}

function getStoredTheme(): "dark" | "light" {
  const v = localStorage.getItem(THEME_KEY);
  return v === "light" ? "light" : "dark";
}

export default function App() {
  const [config, setConfig] = useState<SiteConfig | null>(null);
  const [lang] = useState<Lang>(getStoredLang);
  const [theme, setTheme] = useState<"dark" | "light">(getStoredTheme);

  useEffect(() => {
    loadSiteConfig().then(setConfig);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    localStorage.setItem(THEME_KEY, next);
  };

  if (!config) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--text-muted)",
        }}
      >
        {t(lang, "nav.docs")}
      </div>
    );
  }

  return (
    <>
    <AgentGreeting />
    <Routes>
      <Route
        path="/"
        element={<Home config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />}
      />
      <Route path="/docs" element={<Navigate to="/docs/intro" replace />} />
      <Route
        path="/docs/:slug"
        element={<Docs config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />}
      />
      <Route path="/marketplace" element={<Marketplace config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />} />
      <Route path="/blog" element={<Blog config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />} />
      <Route path="/blog/:slug" element={<Blog config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />} />
      <Route path="/pricing" element={<Pricing config={config} lang={lang} theme={theme} onThemeToggle={toggleTheme} />} />
    </Routes>
    </>
  );
}
