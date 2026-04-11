// filename: hooks/useCompanyPosts.ts
// purpose: Paginated company posts query.
// dependencies: @tanstack/react-query, lib/api

import { useQuery } from "@tanstack/react-query";

import { getCompanyPosts } from "@/lib/api";

export const useCompanyPosts = (company_id: string | null, page: number) => {
  return useQuery({
    queryKey: ["company-posts", company_id, page],
    queryFn: () => getCompanyPosts(company_id as string, 20, page * 20),
    enabled: Boolean(company_id),
    staleTime: 30_000,
    gcTime: 300_000
  });
};
