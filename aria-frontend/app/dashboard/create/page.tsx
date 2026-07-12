import { redirect } from "next/navigation";

export default function LegacyCreatePage() {
  redirect("/posts/new");
}
