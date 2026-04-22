import { create } from "zustand";
import type { AuthTokens, UserPublic } from "../shared/api/auth";

const API_BASE = "http://127.0.0.1:8000/api/v1";

type AuthState = {
  user: UserPublic | null;
  accessToken: string | null;
  refreshToken: string | null;
  loading: boolean;
  setSession: (tokens: AuthTokens) => void;
  clearSession: () => void;
  fetchMe: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
};

const getStoredRefreshToken = () => localStorage.getItem("refresh_token");

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: getStoredRefreshToken(),
  loading: false,

  setSession: (tokens) => {
    localStorage.setItem("refresh_token", tokens.refresh_token);
    set({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token
    });
  },

  clearSession: () => {
    localStorage.removeItem("refresh_token");
    set({ user: null, accessToken: null, refreshToken: null });
  },

  refreshAccessToken: async () => {
    const refreshToken = get().refreshToken ?? getStoredRefreshToken();
    if (!refreshToken) return false;
    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    if (!response.ok) {
      get().clearSession();
      return false;
    }
    const tokens = (await response.json()) as AuthTokens;
    get().setSession(tokens);
    return true;
  },

  fetchMe: async () => {
    set({ loading: true });
    try {
      const token = get().accessToken;
      if (!token) {
        const ok = await get().refreshAccessToken();
        if (!ok) return;
      }
      const accessToken = get().accessToken;
      if (!accessToken) return;
      const response = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      if (response.status === 401) {
        const refreshed = await get().refreshAccessToken();
        if (!refreshed) return;
        return get().fetchMe();
      }
      if (!response.ok) return;
      const me = (await response.json()) as UserPublic;
      set({ user: me });
    } finally {
      set({ loading: false });
    }
  }
}));
