import { getApiUrl, getApiTokenAsync } from "./config";

export function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

async function buildHeaders(method?: string, extra?: HeadersInit): Promise<Headers> {
  const headers = extra instanceof Headers ? extra : new Headers(extra);

  if (method && ["POST", "PUT", "PATCH"].includes(method.toUpperCase())) {
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }

  const token = await getApiTokenAsync();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!method || !["GET", "HEAD", "OPTIONS"].includes(method.toUpperCase())) {
    const csrf = getCsrfToken();
    if (csrf && !headers.has("x-csrf-token")) {
      headers.set("x-csrf-token", csrf);
    }
  }

  return headers;
}

export async function request<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = getApiUrl(path);
  const method = options.method || "GET";
  const headers = await buildHeaders(method, options.headers);

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(
      `Request failed: ${response.status} ${response.statusText}${
        text ? ` - ${text}` : ""
      }`,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) {
    return (await response.text()) as unknown as T;
  }

  return (await response.json()) as T;
}
