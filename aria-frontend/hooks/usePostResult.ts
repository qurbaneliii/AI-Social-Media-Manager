// filename: hooks/usePostResult.ts
// purpose: Poll post generation results until generated/failed and sync global store.
// dependencies: @tanstack/react-query, lib/api, stores/usePostStore

import { useEffect } from "react";

import { useQuery } from "@tanstack/react-query";

import { getPostResult } from "@/lib/api";
import { usePostStore } from "@/stores/usePostStore";

export const usePostResult = (post_id: string | null) => {
  const generationStatus = usePostStore((s) => s.generationStatus);
  const setGeneratedPackage = usePostStore((s) => s.setGeneratedPackage);
  const setGenerationStatus = usePostStore((s) => s.setGenerationStatus);

  const query = useQuery({
    queryKey: ["post-result", post_id],
    queryFn: () => getPostResult(post_id as string),
    enabled: Boolean(post_id),
    refetchInterval: generationStatus === "generating" ? 3000 : false,
    staleTime: 0,
    gcTime: 60_000
  });

  useEffect(() => {
    if (query.data?.status === "generated" && query.data.generated_package_json) {
      setGeneratedPackage(query.data.generated_package_json);
      setGenerationStatus("generated");
      return;
    }
    if (query.data?.status === "failed") {
      setGenerationStatus("failed");
    }
  }, [query.data, setGeneratedPackage, setGenerationStatus]);

  return query;
};
