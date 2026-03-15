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
  consoleUrl: "https://app.prowlrbot.com",
};

let cached: SiteConfig | null = null;

export async function loadSiteConfig(): Promise<SiteConfig> {
  if (cached) return cached;
  try {
    const base = (import.meta.env.BASE_URL ?? "/").replace(/\/$/, "") || "";
    const r = await fetch(`${base}/site.config.json`, { cache: "no-store" });
    if (r.ok) {
      const loaded = (await r.json()) as Partial<SiteConfig>;
      cached = { ...defaultConfig, ...loaded };
      if (!cached.consoleUrl) cached.consoleUrl = defaultConfig.consoleUrl;
      return cached;
    }
  } catch {
    /* use defaults */
  }
  cached = defaultConfig;
  return cached;
}
