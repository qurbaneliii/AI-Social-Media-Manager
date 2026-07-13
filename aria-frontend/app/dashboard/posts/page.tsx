import { redirect } from "next/navigation";

export default function LegacyPostsPage() {
  redirect("/posts");
}
