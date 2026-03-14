export interface SiteConfig {
  projectName: string;
  projectTaglineEn: string;
  projectTaglineZh: string;
  repoUrl: string;
  docsPath: string;
  /** Base URL of the ProwlrBot app (console). Used for Pricing "Upgrade" links. */
  consoleUrl?: string;
}

const defaultConfig: SiteConfig = {
  projectName: "ProwlrBot",
  projectTaglineEn: "Always watching. Always ready.",
  projectTaglineZh: "Always watching. Always ready.",
  repoUrl: "https://github.com/prowlrbot/prowlrbot",
  docsPath: "/docs/",
  consoleUrl: "https://prowlrbot.fly.dev",
};

let cached: SiteConfig | null = null;

export async function loadSiteConfig(): Promise<SiteConfig> {
  if (cached) return cached;
  try {
    const base = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "") || "";
    const r = await fetch(`${base}/site.config.json`);
    if (r.ok) {
      cached = (await r.json()) as SiteConfig;
      return cached;
    }
  } catch {
    /* use defaults */
  }
  return defaultConfig;
}
