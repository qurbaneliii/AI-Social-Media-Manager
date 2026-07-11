import type { UserRole } from "@/types";

import { getDefaultRouteForRole } from "@/lib/navigation";

export const roleRedirectMap: Record<UserRole, string> = {
  agency_admin: getDefaultRouteForRole("agency_admin"),
  brand_manager: getDefaultRouteForRole("brand_manager"),
  content_creator: getDefaultRouteForRole("content_creator"),
  analyst: getDefaultRouteForRole("analyst")
};

export const getRoleRedirectPath = (role: UserRole): string => roleRedirectMap[role];
