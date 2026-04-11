// filename: lib/client-session.ts
// purpose: Browser storage helpers for simple session bootstrap.

import type { UserRole } from "@/types";

export interface ClientSession {
  token: string | null;
  role: UserRole | null;
  companyId: string | null;
}

const KEYS = {
  token: "aria_token",
  role: "aria_role",
  companyId: "aria_company_id"
} as const;

export const getClientSession = (): ClientSession => {
  if (typeof window === "undefined") {
    return { token: null, role: null, companyId: null };
  }
  const roleRaw = localStorage.getItem(KEYS.role);
  const role =
    roleRaw === "agency_admin" ||
    roleRaw === "brand_manager" ||
    roleRaw === "content_creator" ||
    roleRaw === "analyst"
      ? roleRaw
      : null;

  return {
    token: sessionStorage.getItem(KEYS.token) ?? localStorage.getItem(KEYS.token),
    role,
    companyId: localStorage.getItem(KEYS.companyId)
  };
};

export const setClientSession = (input: { token: string; role: UserRole; companyId: string }) => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.setItem(KEYS.token, input.token);
  localStorage.setItem(KEYS.role, input.role);
  localStorage.setItem(KEYS.companyId, input.companyId);
};

export const setClientCompanyId = (companyId: string) => {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(KEYS.companyId, companyId);
};

export const clearClientSession = () => {
  if (typeof window === "undefined") {
    return;
  }
  sessionStorage.removeItem(KEYS.token);
  localStorage.removeItem(KEYS.token);
  localStorage.removeItem(KEYS.role);
  localStorage.removeItem(KEYS.companyId);
};
