import Link from "next/link";

const links = [
  ["Onboarding", "/onboarding"],
  ["Generate", "/generate"],
  ["Schedules", "/schedules"],
  ["Analytics", "/analytics"]
] as const;

export function Nav() {
  return (
    <nav className="flex gap-3 text-sm font-semibold tracking-wide">
      {links.map(([label, href]) => (
        <Link key={href} href={href} className="rounded-full border border-ink/20 bg-white/60 px-4 py-2 hover:bg-white">
          {label}
        </Link>
      ))}
    </nav>
  );
}
