export type Role = "agency_admin" | "brand_manager" | "content_creator" | "analyst";

export const ROLE_LABELS: Record<Role, string> = {
  agency_admin: "Agency Admin",
  brand_manager: "Brand Manager",
  content_creator: "Content Creator",
  analyst: "Analyst"
};

export const ROLE_HOME: Record<Role, string> = {
  agency_admin: "/overview",
  brand_manager: "/posts",
  content_creator: "/posts/new",
  analyst: "/analytics"
};

export const NAV_ITEMS = [
  { label: "Overview", href: "/overview", icon: "LayoutDashboard", roles: ["agency_admin", "brand_manager"] },
  {
    label: "Posts",
    href: "/posts",
    icon: "FileText",
    roles: ["agency_admin", "brand_manager", "content_creator"]
  },
  {
    label: "New Post",
    href: "/posts/new",
    icon: "PenSquare",
    roles: ["agency_admin", "brand_manager", "content_creator"]
  },
  {
    label: "Scheduler",
    href: "/scheduler",
    icon: "CalendarClock",
    roles: ["agency_admin", "brand_manager", "content_creator"]
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: "BarChart2",
    roles: ["agency_admin", "brand_manager", "analyst"]
  },
  { label: "Brand", href: "/settings/brand", icon: "Palette", roles: ["agency_admin", "brand_manager"] },
  { label: "Platforms", href: "/settings/platforms", icon: "Plug", roles: ["agency_admin"] }
] as const;

export function canAccess(role: Role, href: string): boolean {
  const item = NAV_ITEMS.find((n) => n.href === href);
  return item ? (item.roles as readonly string[]).includes(role) : false;
}
