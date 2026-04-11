// filename: stores/useUIStore.ts
// purpose: Pure UI state for tabs, sidebar, and notifications.
// dependencies: zustand, types

import { create } from "zustand";

import type { Platform } from "@/types";

interface UIState {
  activePlatformTab: Platform | null;
  sidebarOpen: boolean;
  activePostResultTab: "variants" | "hashtags" | "audience" | "timing" | "seo" | "quality";
  notificationCount: number;
  setActivePlatformTab: (platform: Platform) => void;
  toggleSidebar: () => void;
  setPostResultTab: (tab: string) => void;
  incrementNotifications: () => void;
  resetNotifications: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activePlatformTab: null,
  sidebarOpen: true,
  activePostResultTab: "variants",
  notificationCount: 0,
  setActivePlatformTab: (platform) => set({ activePlatformTab: platform }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setPostResultTab: (tab) =>
    set({
      activePostResultTab: ["variants", "hashtags", "audience", "timing", "seo", "quality"].includes(tab)
        ? (tab as UIState["activePostResultTab"])
        : "variants"
    }),
  incrementNotifications: () => set((state) => ({ notificationCount: state.notificationCount + 1 })),
  resetNotifications: () => set({ notificationCount: 0 })
}));
