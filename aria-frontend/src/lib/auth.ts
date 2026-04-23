"use client";

const TOKEN_KEY = "aria_token";
const USER_KEY = "aria_user";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: import("./roles").Role;
  company_id: string;
}

export const auth = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getUser: (): AuthUser | null => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setSession: (token: string, user: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  isAuthenticated: () => !!localStorage.getItem(TOKEN_KEY)
};
