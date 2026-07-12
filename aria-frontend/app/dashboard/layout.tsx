import { ProductShell } from "@/components/layout/ProductShell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <ProductShell>{children}</ProductShell>;
}
