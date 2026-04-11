"use client";

import { useMutation } from "@tanstack/react-query";
import { z } from "zod";
import { apiPost } from "../../lib/client";

const ScheduleSchema = z.object({ schedule_ids: z.array(z.string()), status: z.string() });

export default function SchedulesPage() {
  const mutation = useMutation({
    mutationFn: async () =>
      apiPost(
        "/v1/schedules",
        {
          post_id: "00000000-0000-0000-0000-000000000010",
          company_id: "00000000-0000-0000-0000-000000000001",
          targets: [{ platform: "linkedin", run_at_utc: new Date(Date.now() + 3600 * 1000).toISOString() }],
          approval_mode: "human",
          manual_override: { timezone: "UTC", force_window: false }
        },
        ScheduleSchema
      )
  });

  return (
    <section className="space-y-4 rounded-2xl border border-ink/15 bg-white/70 p-6">
      <h2 className="font-display text-3xl">Schedules</h2>
      <button className="rounded-xl bg-accent px-4 py-2 font-semibold text-white" onClick={() => mutation.mutate()}>
        Create Schedule
      </button>
      {mutation.isSuccess && <pre className="text-sm">{JSON.stringify(mutation.data, null, 2)}</pre>}
      {mutation.isError && <p className="text-red-700">{String(mutation.error)}</p>}
    </section>
  );
}
