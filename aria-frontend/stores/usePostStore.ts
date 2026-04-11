// filename: stores/usePostStore.ts
// purpose: Post generation draft and result state.
// dependencies: zustand, types

import { create } from "zustand";

import type { GeneratePostForm, GeneratedPackage } from "@/types";

interface PostState {
  draftForm: Partial<GeneratePostForm>;
  postId: string | null;
  isPolling: boolean;
  generatedPackage: GeneratedPackage | null;
  selectedVariantPerPlatform: Record<string, string>;
  generationStatus: "idle" | "generating" | "generated" | "failed";
  estimatedReadySeconds: number | null;
  setDraftForm: (form: Partial<GeneratePostForm>) => void;
  setPostId: (id: string) => void;
  setGeneratedPackage: (pkg: GeneratedPackage) => void;
  selectVariant: (platform: string, variant_id: string) => void;
  setGenerationStatus: (status: "idle" | "generating" | "generated" | "failed") => void;
  setEstimatedReadySeconds: (seconds: number | null) => void;
  setPolling: (polling: boolean) => void;
  resetPost: () => void;
}

export const usePostStore = create<PostState>((set) => ({
  draftForm: {},
  postId: null,
  isPolling: false,
  generatedPackage: null,
  selectedVariantPerPlatform: {},
  generationStatus: "idle",
  estimatedReadySeconds: null,
  setDraftForm: (form) => set({ draftForm: form }),
  setPostId: (id) => set({ postId: id }),
  setGeneratedPackage: (pkg) => {
    const selected = pkg.variants.reduce<Record<string, string>>((acc, variant) => {
      if (variant.variant_id === pkg.selected_variant_id || !acc[variant.platform]) {
        acc[variant.platform] = variant.variant_id;
      }
      return acc;
    }, {});
    set({ generatedPackage: pkg, selectedVariantPerPlatform: selected });
  },
  selectVariant: (platform, variant_id) =>
    set((state) => ({
      selectedVariantPerPlatform: {
        ...state.selectedVariantPerPlatform,
        [platform]: variant_id
      }
    })),
  setGenerationStatus: (status) => set({ generationStatus: status }),
  setEstimatedReadySeconds: (seconds) => set({ estimatedReadySeconds: seconds }),
  setPolling: (polling) => set({ isPolling: polling }),
  resetPost: () =>
    set({
      draftForm: {},
      postId: null,
      isPolling: false,
      generatedPackage: null,
      selectedVariantPerPlatform: {},
      generationStatus: "idle",
      estimatedReadySeconds: null
    })
}));
