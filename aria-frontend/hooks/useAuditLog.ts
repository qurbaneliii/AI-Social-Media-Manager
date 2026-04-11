// filename: hooks/useAuditLog.ts
// purpose: Query wrapper for audit log retrieval.

import { useQuery } from "@tanstack/react-query";

import { getAuditLog } from "@/lib/api";

export const useAuditLog = (company_id: string | null, page = 0, pageSize = 50) => {
  return useQuery({
    queryKey: ["audit-log", company_id, page, pageSize],
    queryFn: () => getAuditLog(company_id as string, pageSize, page * pageSize),
    enabled: Boolean(company_id),
    staleTime: 30_000,
    gcTime: 300_000
  });
};
