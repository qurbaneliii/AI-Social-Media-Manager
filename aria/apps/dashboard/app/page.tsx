import Link from "next/link";

const cards = [
  { href: "/onboarding", title: "Company Onboarding", subtitle: "Define brand voice and profile." },
  { href: "/generate", title: "Post Generation", subtitle: "Create multi-platform content packages." },
  { href: "/schedules", title: "Schedule Management", subtitle: "Queue approval-aware publish jobs." },
  { href: "/analytics", title: "Analytics", subtitle: "Inspect engagement and learning loops." }
];

export default function HomePage() {
  return (
    <section className="grid gap-4 md:grid-cols-2">
      {cards.map((card) => (
        <Link key={card.href} href={card.href} className="group rounded-2xl border border-ink/15 bg-white/70 p-6 transition hover:-translate-y-0.5 hover:shadow-lg">
          <h2 className="font-display text-2xl text-accent">{card.title}</h2>
          <p className="mt-2 text-muted">{card.subtitle}</p>
        </Link>
      ))}
    </section>
  );
}
