import { redirect } from "next/navigation";

export default function LegacyContentStudioPage() {
  redirect("/posts/new");
}
