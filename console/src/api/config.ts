declare const BASE_URL: string;
declare const TOKEN: string;

/**
 * Get the full API URL with /api prefix
 * @param path - API path (e.g., "/models", "/skills")
 * @returns Full API URL (e.g., "http://localhost:8088/api/models" or "/api/models")
 */
export function getApiUrl(path: string): string {
  const base = typeof BASE_URL !== "undefined" ? BASE_URL : "";
  const apiPrefix = "/api";
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${base}${apiPrefix}${normalizedPath}`;
}

/**
 * ROAR protocol SSE stream URL (same origin; Vite proxies /roar to backend).
 */
export function getRoarEventsUrl(): string {
  const base = typeof BASE_URL !== "undefined" ? BASE_URL : "";
  return `${base}/roar/events`;
}

/**
 * Get the API token.
 *
 * Checks for a JWT in localStorage first (set after login), then falls back
 * to the build-time TOKEN constant for legacy API-token auth.
 */
export function getApiToken(): string {
  const jwt = localStorage.getItem("prowlrbot-jwt");
  if (jwt) return jwt;
  return typeof TOKEN !== "undefined" ? TOKEN : "";
}
