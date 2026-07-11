import {
  BarChart2,
  Brain,
  Calendar,
  FileText,
  LayoutDashboard,
  MoreHorizontal,
  PlusCircle,
  Settings,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { UserRole } from "@/types";

export type NavigationItemId =
  | "overview"
  | "brand-brain"
  | "create"
  | "content"
  | "calendar"
  | "approval"
  | "insights"
  | "settings"
  | "more";

export interface NavigationItem {
  id: NavigationItemId;
  label: string;
  href: string;
  icon: LucideIcon;
  roles: UserRole[];
  section: "main" | "settings" | "mobile";
  highlight?: boolean;
}

const ALL_ROLES: UserRole[] = ["agency_admin", "brand_manager", "content_creator", "analyst"];
const OPERATOR_ROLES: UserRole[] = ["agency_admin", "brand_manager", "content_creator"];
const INSIGHT_ROLES: UserRole[] = ["agency_admin", "brand_manager", "analyst"];

export const NAVIGATION_ITEMS: NavigationItem[] = [
  {
    id: "overview",
    label: "Overview",
    href: "/dashboard/brand",
    icon: LayoutDashboard,
    roles: ALL_ROLES,
    section: "main",
  },
  {
    id: "brand-brain",
    label: "Brand Brain",
    href: "/dashboard/brand-brain",
    icon: Brain,
    roles: OPERATOR_ROLES,
    section: "main",
  },
  {
    id: "create",
    label: "Create",
    href: "/posts/new",
    icon: PlusCircle,
    roles: OPERATOR_ROLES,
    section: "main",
    highlight: true,
  },
  {
    id: "content",
    label: "Content",
    href: "/posts",
    icon: FileText,
    roles: ALL_ROLES,
    section: "main",
  },
  {
    id: "calendar",
    label: "Calendar",
    href: "/scheduler",
    icon: Calendar,
    roles: OPERATOR_ROLES,
    section: "main",
  },
  {
    id: "approval",
    label: "Approval",
    href: "/dashboard/approval",
    icon: ShieldCheck,
    roles: OPERATOR_ROLES,
    section: "main",
  },
  {
    id: "insights",
    label: "Insights",
    href: "/analytics",
    icon: BarChart2,
    roles: INSIGHT_ROLES,
    section: "main",
  },
  {
    id: "settings",
    label: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
    roles: ALL_ROLES,
    section: "settings",
  },
  {
    id: "more",
    label: "More",
    href: "/dashboard/settings",
    icon: MoreHorizontal,
    roles: ALL_ROLES,
    section: "mobile",
  },
];

const MOBILE_PRIMARY_IDS: NavigationItemId[] = ["overview", "create", "content", "approval", "more"];
const MOBILE_PRIMARY_ROUTE_IDS = new Set<NavigationItemId>(["overview", "create", "content", "approval"]);

export const isActiveRoute = (pathname: string, href: string): boolean => {
  if (href === "/posts" && pathname === "/posts/new") {
    return false;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
};

export const canRoleAccessNavigationItem = (role: UserRole | null | undefined, item: NavigationItem): boolean => {
  if (!role) {
    return true;
  }
  return item.roles.includes(role);
};

export const getNavigationItems = (role?: UserRole | null): NavigationItem[] => {
  return NAVIGATION_ITEMS.filter((item) => item.section !== "mobile" && canRoleAccessNavigationItem(role, item));
};

export const getNavigationSections = (role?: UserRole | null) => {
  const items = getNavigationItems(role);
  return [
    { label: "Main", items: items.filter((item) => item.section === "main") },
    { label: "Settings", items: items.filter((item) => item.section === "settings") },
  ].filter((section) => section.items.length > 0);
};

export const getMobileNavigationItems = (role?: UserRole | null): NavigationItem[] => {
  return MOBILE_PRIMARY_IDS.map((id) => NAVIGATION_ITEMS.find((item) => item.id === id))
    .filter((item): item is NavigationItem => Boolean(item))
    .filter((item) => canRoleAccessNavigationItem(role, item));
};

export const getMobileMoreNavigationItems = (role?: UserRole | null): NavigationItem[] => {
  return getNavigationItems(role).filter((item) => !MOBILE_PRIMARY_ROUTE_IDS.has(item.id));
};

export const getDefaultRouteForRole = (role: UserRole): string => {
  return getNavigationItems(role)[0]?.href ?? "/posts";
};
