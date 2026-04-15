import type { UserRole } from "@/types";

export const roleRedirectMap: Record<UserRole, string> = {
  agency_admin: "/posts/new",
  brand_manager: "/posts/new",
  content_creator: "/posts/new",
  analyst: "/analytics"
};

export const getRoleRedirectPath = (role: UserRole): string => roleRedirectMap[role];
