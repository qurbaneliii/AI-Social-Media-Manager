// filename: stores/useSchedulerStore.ts
// purpose: Scheduling selection and request assembly state.
// dependencies: zustand, types

import { create } from "zustand";

import type { Platform, PostingWindow, ScheduleTarget } from "@/types";

interface SchedulerState {
  scheduleTargets: ScheduleTarget[];
  approvalMode: "human" | "auto";
  selectedWindows: Record<Platform, PostingWindow | null>;
  manualOverrides: Record<Platform, string | null>;
  scheduleIds: string[];
  addTarget: (target: ScheduleTarget) => void;
  removeTarget: (platform: Platform) => void;
  setApprovalMode: (mode: "human" | "auto") => void;
  selectWindow: (platform: Platform, window: PostingWindow) => void;
  setManualOverride: (platform: Platform, datetime: string) => void;
  setScheduleIds: (ids: string[]) => void;
  resetScheduler: () => void;
}

const initialWindows: Record<Platform, PostingWindow | null> = {
  instagram: null,
  linkedin: null,
  facebook: null,
  x: null,
  tiktok: null,
  pinterest: null
};

const initialOverrides: Record<Platform, string | null> = {
  instagram: null,
  linkedin: null,
  facebook: null,
  x: null,
  tiktok: null,
  pinterest: null
};

export const useSchedulerStore = create<SchedulerState>((set) => ({
  scheduleTargets: [],
  approvalMode: "human",
  selectedWindows: initialWindows,
  manualOverrides: initialOverrides,
  scheduleIds: [],
  addTarget: (target) =>
    set((state) => ({
      scheduleTargets: [...state.scheduleTargets.filter((x) => x.platform !== target.platform), target]
    })),
  removeTarget: (platform) =>
    set((state) => ({
      scheduleTargets: state.scheduleTargets.filter((item) => item.platform !== platform)
    })),
  setApprovalMode: (mode) => set({ approvalMode: mode }),
  selectWindow: (platform, window) =>
    set((state) => ({
      selectedWindows: {
        ...state.selectedWindows,
        [platform]: window
      }
    })),
  setManualOverride: (platform, datetime) =>
    set((state) => ({
      manualOverrides: {
        ...state.manualOverrides,
        [platform]: datetime
      }
    })),
  setScheduleIds: (ids) => set({ scheduleIds: ids }),
  resetScheduler: () =>
    set({
      scheduleTargets: [],
      approvalMode: "human",
      selectedWindows: initialWindows,
      manualOverrides: initialOverrides,
      scheduleIds: []
    })
}));
