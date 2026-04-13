import type { UserRole } from "@/types";

export const roleRedirectMap: Record<UserRole, string> = {
  agency_admin: "/dashboard/admin",
  brand_manager: "/dashboard/brand",
  content_creator: "/dashboard/content",
  analyst: "/dashboard/analytics"
};

export const getRoleRedirectPath = (role: UserRole): string => roleRedirectMap[role];
