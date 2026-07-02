import { create } from "zustand";

export type Role = "admin" | "doctor" | "patient";

interface AuthState {
  userId: string | null;
  role: Role | null;
  fullName: string | null;
  isAuthenticated: boolean;
  hydrate: () => void;
  login: (params: { userId: string; role: Role; accessToken: string; refreshToken: string; fullName?: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  userId: null,
  role: null,
  fullName: null,
  isAuthenticated: false,

  hydrate: () => {
    if (typeof window === "undefined") return;
    const userId = localStorage.getItem("user_id");
    const role = localStorage.getItem("role") as Role | null;
    const fullName = localStorage.getItem("full_name");
    if (userId && role) {
      set({ userId, role, fullName, isAuthenticated: true });
    }
  },

  login: ({ userId, role, accessToken, refreshToken, fullName }) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("user_id", userId);
    localStorage.setItem("role", role);
    if (fullName) localStorage.setItem("full_name", fullName);
    set({ userId, role, fullName: fullName || null, isAuthenticated: true });
  },

  logout: () => {
    localStorage.clear();
    set({ userId: null, role: null, fullName: null, isAuthenticated: false });
  },
}));
