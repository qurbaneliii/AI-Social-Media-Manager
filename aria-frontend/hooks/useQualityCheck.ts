// filename: hooks/useQualityCheck.ts
// purpose: Mutation wrapper for onboarding quality-check trigger.

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError, triggerQualityCheck } from "@/lib/api";

export const useQualityCheck = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["quality-check"],
    mutationFn: (company_id: string) => triggerQualityCheck(company_id),
    onSuccess: (_data, company_id) => {
      queryClient.invalidateQueries({ queryKey: ["onboarding-status", company_id] });
      toast.success("Quality check started");
    },
    onError: (error) => {
      const err = error as ApiError;
      toast.error(err.message || "Failed to start quality check");
    }
  });
};
