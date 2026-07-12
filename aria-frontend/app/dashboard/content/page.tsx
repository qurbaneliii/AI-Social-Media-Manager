import { redirect } from "next/navigation";

export default function LegacyContentDashboardPage() {
  redirect("/posts");
}
