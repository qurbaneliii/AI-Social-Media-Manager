export default function AnalyticsPage() {
  return (
    <section className="grid gap-4 md:grid-cols-3">
      <article className="rounded-2xl border border-ink/15 bg-white/70 p-6">
        <h3 className="text-sm uppercase tracking-wide text-muted">Engagement Rate</h3>
        <p className="mt-3 font-display text-4xl text-accent">7.4%</p>
      </article>
      <article className="rounded-2xl border border-ink/15 bg-white/70 p-6">
        <h3 className="text-sm uppercase tracking-wide text-muted">CTR</h3>
        <p className="mt-3 font-display text-4xl text-accent">1.9%</p>
      </article>
      <article className="rounded-2xl border border-ink/15 bg-white/70 p-6">
        <h3 className="text-sm uppercase tracking-wide text-muted">Follower Delta</h3>
        <p className="mt-3 font-display text-4xl text-accent">+34</p>
      </article>
    </section>
  );
}
