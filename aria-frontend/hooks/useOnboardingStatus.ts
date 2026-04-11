// filename: hooks/useOnboardingStatus.ts
// purpose: Poll onboarding status and synchronize progress in global company store.
// dependencies: @tanstack/react-query, lib/api, stores/useCompanyStore

import { useEffect } from "react";

import { useQuery } from "@tanstack/react-query";

import { getOnboardingStatus } from "@/lib/api";
import { useCompanyStore } from "@/stores/useCompanyStore";

export const useOnboardingStatus = (company_id: string | null) => {
  const setOnboardingProgress = useCompanyStore((s) => s.setOnboardingProgress);

  const query = useQuery({
    queryKey: ["onboarding-status", company_id],
    queryFn: () => getOnboardingStatus(company_id as string),
    enabled: Boolean(company_id),
    refetchInterval: (queryState) => {
      const step = queryState.state.data?.step ?? 11;
      return step < 11 ? 5000 : false;
    },
    staleTime: 0,
    gcTime: 30_000
  });

  useEffect(() => {
    if (query.data) {
      setOnboardingProgress(query.data);
    }
  }, [query.data, setOnboardingProgress]);

  return {
    status: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch
  };
};
