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
 * When Clerk is used, the app sets a token provider so API requests send
 * the Clerk session JWT. Otherwise we use localStorage or build-time TOKEN.
 */
let tokenProvider: (() => Promise<string | null>) | null = null;

export function setTokenProvider(fn: () => Promise<string | null>): void {
  tokenProvider = fn;
}

/**
 * Get the API token (sync). Prefer getApiTokenAsync() when Clerk is used.
 * Returns localStorage JWT or legacy TOKEN; Clerk token is provided via getApiTokenAsync.
 */
export function getApiToken(): string {
  const jwt = localStorage.getItem("prowlrbot-jwt");
  if (jwt) return jwt;
  return typeof TOKEN !== "undefined" ? TOKEN : "";
}

/**
 * Get the API token, resolving Clerk session token when a provider is set.
 * Use this in request builders so Clerk JWTs are sent to the backend.
 */
export async function getApiTokenAsync(): Promise<string> {
  if (tokenProvider) {
    const clerkToken = await tokenProvider();
    if (clerkToken) return clerkToken;
  }
  return getApiToken();
}
