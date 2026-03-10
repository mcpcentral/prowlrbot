export interface SiteConfig {
  projectName: string;
  projectTaglineEn: string;
  projectTaglineZh: string;
  repoUrl: string;
  docsPath: string;
}

const defaultConfig: SiteConfig = {
  projectName: "ProwlrBot",
  projectTaglineEn: "Always watching. Always ready.",
  projectTaglineZh: "Always watching. Always ready.",
  repoUrl: "https://github.com/mcpcentral/prowlrbot",
  docsPath: "/docs/",
};

let cached: SiteConfig | null = null;

export async function loadSiteConfig(): Promise<SiteConfig> {
  if (cached) return cached;
  try {
    const r = await fetch("/site.config.json");
    if (r.ok) {
      cached = (await r.json()) as SiteConfig;
      return cached;
    }
  } catch {
    /* use defaults */
  }
  return defaultConfig;
}
