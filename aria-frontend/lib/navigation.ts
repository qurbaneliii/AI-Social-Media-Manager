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
  mobile: "primary" | "more" | false;
  commandShortcut: string;
  breadcrumbLabel: string;
  pageTitle: string;
  description: string;
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
    mobile: "primary",
    commandShortcut: "G O",
    breadcrumbLabel: "Overview",
    pageTitle: "Overview",
    description: "Operational priorities, recent content, and workspace readiness.",
  },
  {
    id: "brand-brain",
    label: "Brand Brain",
    href: "/dashboard/brand-brain",
    icon: Brain,
    roles: OPERATOR_ROLES,
    section: "main",
    mobile: "more",
    commandShortcut: "G B",
    breadcrumbLabel: "Brand Brain",
    pageTitle: "Brand Brain",
    description: "Brand identity, audience, language, claims, and platform context.",
  },
  {
    id: "create",
    label: "Create",
    href: "/posts/new",
    icon: PlusCircle,
    roles: OPERATOR_ROLES,
    section: "main",
    mobile: "primary",
    commandShortcut: "G C",
    breadcrumbLabel: "Create",
    pageTitle: "Create",
    description: "Build, refine, review, and save approval-ready social content.",
    highlight: true,
  },
  {
    id: "content",
    label: "Content",
    href: "/posts",
    icon: FileText,
    roles: ALL_ROLES,
    section: "main",
    mobile: "primary",
    commandShortcut: "G P",
    breadcrumbLabel: "Content",
    pageTitle: "Content Library",
    description: "Search and manage drafts, variants, ownership, and approval state.",
  },
  {
    id: "calendar",
    label: "Calendar",
    href: "/scheduler",
    icon: Calendar,
    roles: OPERATOR_ROLES,
    section: "main",
    mobile: "more",
    commandShortcut: "G K",
    breadcrumbLabel: "Calendar",
    pageTitle: "Calendar",
    description: "Plan approved content and distinguish readiness from external scheduling.",
  },
  {
    id: "approval",
    label: "Approval",
    href: "/dashboard/approval",
    icon: ShieldCheck,
    roles: OPERATOR_ROLES,
    section: "main",
    mobile: "primary",
    commandShortcut: "G A",
    breadcrumbLabel: "Approval",
    pageTitle: "Approval",
    description: "Review content, quality, requested changes, and trusted audit history.",
  },
  {
    id: "insights",
    label: "Insights",
    href: "/analytics",
    icon: BarChart2,
    roles: INSIGHT_ROLES,
    section: "main",
    mobile: "more",
    commandShortcut: "G I",
    breadcrumbLabel: "Insights",
    pageTitle: "Insights",
    description: "Understand performance with explicit source and confidence labels.",
  },
  {
    id: "settings",
    label: "Settings",
    href: "/dashboard/settings",
    icon: Settings,
    roles: ALL_ROLES,
    section: "settings",
    mobile: "more",
    commandShortcut: "G S",
    breadcrumbLabel: "Settings",
    pageTitle: "Settings",
    description: "Manage account, workspace, security, AI status, and diagnostics.",
  },
  {
    id: "more",
    label: "More",
    href: "/dashboard/settings",
    icon: MoreHorizontal,
    roles: ALL_ROLES,
    section: "mobile",
    mobile: "primary",
    commandShortcut: "",
    breadcrumbLabel: "More",
    pageTitle: "More",
    description: "Open secondary workspace destinations.",
  },
];

const MOBILE_PRIMARY_IDS: NavigationItemId[] = ["overview", "create", "content", "approval", "more"];

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
  return getNavigationItems(role).filter((item) => item.mobile === "more");
};

export const getCommandNavigationItems = (role?: UserRole | null): NavigationItem[] => {
  return getNavigationItems(role).filter((item) => item.commandShortcut);
};

export const getActiveNavigationItem = (
  pathname: string,
  role?: UserRole | null
): NavigationItem | undefined => {
  return getNavigationItems(role).find((item) => isActiveRoute(pathname, item.href));
};

export const getDefaultRouteForRole = (role: UserRole): string => {
  return getNavigationItems(role)[0]?.href ?? "/posts";
};
