"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { AUTH_PREVIEW_MESSAGE, PREVIEW_USER_STORAGE_KEY, mockUser } from "@/lib/mockData";
import { IS_STATIC } from "@/lib/isStatic";
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
  logout: () => Promise<void>;
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

  const loadPreviewUser = useCallback((): AuthUser | null => {
    if (typeof window === "undefined") {
      return null;
    }

    const raw = localStorage.getItem(PREVIEW_USER_STORAGE_KEY);
    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as AuthUser;
    } catch {
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    if (IS_STATIC) {
      setUser(loadPreviewUser());
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/auth/me", {
        method: "GET",
        credentials: "include"
      });

      if (!response.ok) {
        setUser(null);
        return;
      }

      const payload = (await response.json()) as { user: AuthUser };
      setUser(payload.user);
    } finally {
      setIsLoading(false);
    }
  }, [loadPreviewUser]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (input: LoginInput) => {
    if (IS_STATIC) {
      throw new Error(AUTH_PREVIEW_MESSAGE);
    }

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
    setUser(payload.user);
    return payload.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    if (IS_STATIC) {
      throw new Error(AUTH_PREVIEW_MESSAGE);
    }

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

  const logout = useCallback(async () => {
    if (IS_STATIC) {
      if (typeof window !== "undefined") {
        localStorage.removeItem(PREVIEW_USER_STORAGE_KEY);
      }
      setUser(null);
      return;
    }

    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include"
    });
    setUser(null);
  }, []);

  const continueAsPreviewUser = useCallback(() => {
    if (typeof window === "undefined") {
      return;
    }

    localStorage.setItem(PREVIEW_USER_STORAGE_KEY, JSON.stringify(mockUser));
    localStorage.setItem("aria_company_id", "preview-company");
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
