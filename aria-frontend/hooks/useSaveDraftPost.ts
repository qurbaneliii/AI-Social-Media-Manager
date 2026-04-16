// filename: hooks/useSaveDraftPost.ts
// purpose: Save generated content as a persistent backend draft post.

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { saveDraftPost, type SaveDraftRequest } from "@/lib/api";

export const useSaveDraftPost = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationKey: ["save-draft-post"],
    mutationFn: (payload: SaveDraftRequest) => saveDraftPost(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["company-posts"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-feed"] });
    }
  });
};
