// filename: hooks/useGeneratePost.ts
// purpose: Mutation wrapper for post generation requests.
// dependencies: @tanstack/react-query, sonner, lib/api, stores/usePostStore

import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError, generatePost } from "@/lib/api";
import { usePostStore } from "@/stores/usePostStore";
import type { GeneratePostForm } from "@/types";

export const useGeneratePost = () => {
  const setPostId = usePostStore((s) => s.setPostId);
  const setGenerationStatus = usePostStore((s) => s.setGenerationStatus);
  const setEstimatedReadySeconds = usePostStore((s) => s.setEstimatedReadySeconds);

  return useMutation({
    mutationKey: ["generate-post"],
    mutationFn: (data: GeneratePostForm) => generatePost(data),
    onSuccess: (data) => {
      setPostId(data.post_id);
      setGenerationStatus("generating");
      setEstimatedReadySeconds(data.estimated_ready_seconds);
    },
    onError: (error) => {
      const err = error as ApiError;
      if (err.code === "HTTP_429") {
        const retryAfter = Number((err.details as { retry_after?: number } | undefined)?.retry_after ?? 0);
        toast.error(`Generation limit reached (20/min). Try again in ${retryAfter}s.`);
        return;
      }
      toast.error(err.message);
    }
  });
};
