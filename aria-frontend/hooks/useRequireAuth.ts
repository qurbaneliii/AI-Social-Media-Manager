"use client";

import { useEffect } from "react";

import { useAuth } from "@/context/AuthContext";
import { getBasePath } from "@/lib/navigate";

export const useRequireAuth = () => {
  const auth = useAuth();

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const user = localStorage.getItem("user");
    const token = localStorage.getItem("token") ?? localStorage.getItem("aria_token");
    if (!user || !token) {
      window.location.href = `${getBasePath()}/login`;
      return;
    }

    try {
      JSON.parse(user);
    } catch {
      window.location.href = `${getBasePath()}/login`;
      return;
    }

    if (!auth.user) {
      void auth.refreshUser();
    }
  }, [auth.refreshUser, auth.user]);

  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated && typeof window !== "undefined") {
      window.location.href = `${getBasePath()}/login`;
    }
  }, [auth.isAuthenticated, auth.isLoading]);

  return auth;
};
