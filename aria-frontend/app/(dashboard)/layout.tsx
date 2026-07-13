import { ProductShell } from "@/components/layout/ProductShell";

export default function DashboardRouteGroupLayout({ children }: { children: React.ReactNode }) {
  return <ProductShell>{children}</ProductShell>;
}
