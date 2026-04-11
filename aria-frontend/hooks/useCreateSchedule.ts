// filename: hooks/useCreateSchedule.ts
// purpose: Mutation wrapper for schedule creation with conflict handling.
// dependencies: @tanstack/react-query, sonner, lib/api, stores/useSchedulerStore

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError, createSchedule } from "@/lib/api";
import { useSchedulerStore } from "@/stores/useSchedulerStore";
import type { ScheduleRequest } from "@/types";

export const useCreateSchedule = () => {
  const setScheduleIds = useSchedulerStore((s) => s.setScheduleIds);

  return useMutation({
    mutationKey: ["create-schedule"],
    mutationFn: (data: ScheduleRequest) => createSchedule(data),
    onSuccess: (data) => {
      setScheduleIds(data.schedule_ids);
      toast.success(`Schedule queued: ${data.schedule_ids.join(", ")}`);
    },
    onError: (error) => {
      const err = error as ApiError;
      if (err.code === "SCHEDULE_COLLISION" || err.code === "HTTP_409") {
        toast.error(`Scheduling conflict detected. ${JSON.stringify(err.details ?? {})}`);
        return;
      }
      toast.error(err.message || "Failed to create schedule");
    }
  });
};
