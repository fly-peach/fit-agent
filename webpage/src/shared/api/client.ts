import type { AuthTokens, LoginPayload, RegisterPayload, RegisterResponse, UserPublic } from "./auth";
import { useAuthStore } from "../../store/auth";

const API_BASE = "http://127.0.0.1:8000/api/v1";

function extractErrorMessage(raw: unknown): string {
  if (typeof raw === "string" && raw.trim()) return raw;
  if (raw && typeof raw === "object" && "detail" in raw) {
    const detail = (raw as { detail?: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: string } | undefined;
      if (first?.msg) return first.msg;
    }
  }
  return "请求失败，请稍后重试";
}

async function buildApiError(response: Response): Promise<Error> {
  try {
    const data = (await response.json()) as unknown;
    return new Error(extractErrorMessage(data));
  } catch {
    const text = await response.text();
    return new Error(extractErrorMessage(text));
  }
}

export async function register(payload: RegisterPayload): Promise<RegisterResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw await buildApiError(response);
  }
  return (await response.json()) as RegisterResponse;
}

export async function login(payload: LoginPayload): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw await buildApiError(response);
  }
  return (await response.json()) as AuthTokens;
}

export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const store = useAuthStore.getState();
  let accessToken = store.accessToken;
  if (!accessToken) {
    const refreshed = await store.refreshAccessToken();
    if (!refreshed) {
      store.clearSession();
      throw new Error("未登录或登录已过期");
    }
    accessToken = useAuthStore.getState().accessToken;
  }

  const headers = new Headers(options.headers || {});
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Try to refresh once
    const refreshed = await store.refreshAccessToken();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${useAuthStore.getState().accessToken}`);
      return fetch(`${API_BASE}${url}`, { ...options, headers });
    } else {
      store.clearSession();
      throw new Error("登录已过期，请重新登录");
    }
  }

  if (!response.ok) {
    throw await buildApiError(response);
  }

  return response;
}

export async function fetchMeWithStore(): Promise<UserPublic> {
  const response = await fetchWithAuth("/auth/me");
  return (await response.json()) as UserPublic;
}
