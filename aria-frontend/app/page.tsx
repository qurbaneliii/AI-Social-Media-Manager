// filename: app/page.tsx
// purpose: Entry route redirect.

import { redirect } from "next/navigation";

export default function HomePage() {
  redirect("/signin");
}
