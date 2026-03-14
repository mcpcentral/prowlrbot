#!/usr/bin/env node
/**
 * After vite build, copy index.html into docs/ and docs/<slug>/ so that
 * static hosts (e.g. GitHub Pages) serve the SPA for each route without
 * needing a Node server. Must match DOC_SLUGS in src/pages/Docs.tsx and
 * BLOG_FILES in src/pages/Blog.tsx.
 */
import { mkdir, readFile, writeFile } from "fs/promises";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const distDir = join(__dirname, "..", "dist");

const DOC_SLUGS = [
  "intro",
  "quickstart",
  "console",
  "channels",
  "skills",
  "mcp",
  "memory",
  "compact",
  "commands",
  "heartbeat",
  "config",
  "cli",
  "marketplace",
  "agents-external",
  "teams",
  "credits",
  "guide-tiers-and-payments",
  "guide-monitoring",
  "guide-cron-jobs",
  "guide-deployment",
  "guide-memory-system",
  "guide-mcp-setup",
  "guide-war-room-mcp-debug",
  "guide-war-room-dashboard-plan",
  "guide-providers",
  "guide-cli-reference",
  "guide-channels",
  "guide-skills",
  "guide-marketplace",
  "guide-env-and-console-login",
  "guide-acp-ide-integration",
  "guide-console-plugins-marketplace",
  "guide-marketplace-repo-upgrade",
  "guide-cross-network-connectivity",
  "guide-cross-network-setup",
  "guide-roar-usage",
  "faq",
  "community",
  "contributing",
  "roadmap",
  "privacy",
  "terms",
];

const BLOG_SLUGS = [
  "2026-03-11-pip-install-broke-my-wsl",
  "2026-03-10-whats-coming-next",
  "2026-03-10-war-room-is-live",
  "2026-03-10-setting-up-your-first-swarm",
  "2026-03-10-security-first",
  "2026-03-10-introducing-prowlrbot",
];

async function main() {
  const indexHtml = await readFile(join(distDir, "index.html"), "utf-8");
  const paths = [
    "docs",
    "docs/search",
    ...DOC_SLUGS.map((s) => `docs/${s}`),
    "blog",
    ...BLOG_SLUGS.map((s) => `blog/${s}`),
    "marketplace",
    "pricing",
    "sign-in",
    "sign-in/sso-callback",
    "sign-up",
    "sign-up/sso-callback",
  ];
  for (const p of paths) {
    const out = join(distDir, p, "index.html");
    await mkdir(dirname(out), { recursive: true });
    await writeFile(out, indexHtml);
  }
  console.log(`[spa-fallback-pages] Wrote index.html for ${paths.length} routes`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
