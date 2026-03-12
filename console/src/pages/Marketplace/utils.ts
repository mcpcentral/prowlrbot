import type { MarketplaceListing } from "./types";

/**
 * Transform a backend listing (snake_case) into frontend format (camelCase).
 */
export function transformListing(raw: Record<string, any>): MarketplaceListing {
  return {
    id: raw.id,
    title: raw.title,
    name: raw.title,
    description: raw.description ?? "",
    category: raw.category ?? "skills",
    version: raw.version ?? "1.0.0",
    rating: raw.rating ?? 0,
    ratingCount: raw.ratings_count ?? raw.ratingCount ?? 0,
    downloads: raw.downloads ?? 0,
    price: raw.price ?? 0,
    tags: raw.tags ?? [],
    trustTier: raw.trust_tier ?? raw.trustTier ?? "verified",
    authorName: raw.author_name ?? raw.authorName ?? raw.author_id ?? "",
    authorUrl: raw.author_url ?? raw.authorUrl ?? "",
    authorAvatarUrl: raw.author_avatar_url ?? raw.authorAvatarUrl ?? "",
    sourceRepo: raw.source_repo ?? raw.sourceRepo ?? "",
    license: raw.license ?? "MIT",
    changelog: raw.changelog ?? "",
    compatibility: raw.compatibility ?? "",
    difficulty: raw.difficulty ?? "beginner",
    installed: raw.installed,
  };
}

export function formatDownloads(count: number): string {
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
  return String(count);
}

export const CATEGORY_COLORS: Record<string, string> = {
  skills: "cyan",
  agents: "purple",
  prompts: "gold",
  "mcp-servers": "blue",
  themes: "magenta",
  workflows: "geekblue",
  specs: "orange",
};

export const CATEGORY_LABELS: Record<string, string> = {
  skills: "Skills",
  agents: "Agents",
  prompts: "Prompts",
  "mcp-servers": "MCP Servers",
  themes: "Themes",
  workflows: "Workflows",
  specs: "Specs",
};
