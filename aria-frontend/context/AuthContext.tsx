"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { mockUser, PREVIEW_COMPANY_ID } from "@/lib/mockData";
import { getBasePath } from "@/lib/navigate";
import type { UserRole } from "@/types";

interface AuthUser {
  id: string;
  email: string;
  name: string | null;
  role: UserRole;
}

interface LoginInput {
  email: string;
  password: string;
}

interface RegisterInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (input: LoginInput) => Promise<AuthUser>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  continueAsPreviewUser: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const parseErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as { error?: string };
    return payload.error ?? "Request failed";
  } catch {
    return "Request failed";
  }
};

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const readUserFromStorage = useCallback((): AuthUser | null => {
    if (typeof window === "undefined") {
      return null;
    }

    const stored = localStorage.getItem("user");
    const token = localStorage.getItem("token");
    if (!stored || !token) {
      return null;
    }

    try {
      return JSON.parse(stored) as AuthUser;
    } catch {
      localStorage.clear();
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(readUserFromStorage());
    setIsLoading(false);
  }, [readUserFromStorage]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const stored = localStorage.getItem("user");
      const token = localStorage.getItem("token");
      if (stored && token) {
        setUser(JSON.parse(stored) as AuthUser);
      }
    } catch {
      localStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (input: LoginInput) => {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      credentials: "include",
      body: JSON.stringify(input)
    });

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
    }

    const payload = (await response.json()) as { user: AuthUser; token: string };
    if (typeof window !== "undefined") {
      localStorage.setItem("user", JSON.stringify(payload.user));
      localStorage.setItem("token", payload.token);
    }
    setUser(payload.user);
    return payload.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(input)
    });

    if (!response.ok) {
      throw new Error(await parseErrorMessage(response));
    }
  }, []);

  const logout = useCallback(() => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("user");
      localStorage.removeItem("token");
      localStorage.removeItem("isPreview");
      window.location.href = `${getBasePath()}/login`;
    }
    setUser(null);
  }, []);

  const continueAsPreviewUser = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    localStorage.setItem("user", JSON.stringify(mockUser));
    localStorage.setItem("token", "preview-token-static-mode");
    localStorage.setItem("isPreview", "true");
    localStorage.setItem("aria_company_id", PREVIEW_COMPANY_ID);
    localStorage.setItem("aria_role", mockUser.role);
    setUser(mockUser);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
      refreshUser,
      continueAsPreviewUser
    }),
    [continueAsPreviewUser, isLoading, login, logout, refreshUser, register, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
