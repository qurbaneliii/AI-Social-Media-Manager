"use client";

import { create } from "zustand";

import {
  defaultBrandProfile,
  type BrandProfile,
  type DashboardNotification,
  type DashboardPost
} from "@/lib/mock-data";

interface DashboardState {
  sidebarCollapsed: boolean;
  mobileNavOpen: boolean;
  commandPaletteOpen: boolean;
  notifications: DashboardNotification[];
  dismissedNotificationIds: string[];
  posts: DashboardPost[];
  brandProfile: BrandProfile;
  setSidebarCollapsed: (value: boolean) => void;
  setMobileNavOpen: (value: boolean) => void;
  setCommandPaletteOpen: (value: boolean) => void;
  setPosts: (items: DashboardPost[]) => void;
  hydrateNotifications: (items: DashboardNotification[]) => void;
  clearDashboardData: () => void;
  markNotificationRead: (id: string) => void;
  markAllNotificationsRead: () => void;
  dismissNotification: (id: string) => void;
  updateCompanyName: (name: string) => void;
  updateBrandProfile: (next: Partial<BrandProfile>) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  sidebarCollapsed: false,
  mobileNavOpen: false,
  commandPaletteOpen: false,
  notifications: [],
  dismissedNotificationIds: [],
  posts: [],
  brandProfile: defaultBrandProfile,
  setSidebarCollapsed: (value) => set({ sidebarCollapsed: value }),
  setMobileNavOpen: (value) => set({ mobileNavOpen: value }),
  setCommandPaletteOpen: (value) => set({ commandPaletteOpen: value }),
  setPosts: (items) => set({ posts: items }),
  hydrateNotifications: (items) =>
    set((state) => {
      const existingById = new Map(state.notifications.map((notification) => [notification.id, notification]));
      const next = items
        .filter((notification) => !state.dismissedNotificationIds.includes(notification.id))
        .map((notification) => {
          const current = existingById.get(notification.id);
          return {
            ...notification,
            read: current?.read ?? notification.read
          };
        });
      return { notifications: next };
    }),
  clearDashboardData: () => set({ notifications: [], posts: [], dismissedNotificationIds: [] }),
  markNotificationRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((item) => (item.id === id ? { ...item, read: true } : item))
    })),
  markAllNotificationsRead: () =>
    set((state) => ({
      notifications: state.notifications.map((item) => ({ ...item, read: true }))
    })),
  dismissNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((item) => item.id !== id),
      dismissedNotificationIds: state.dismissedNotificationIds.includes(id)
        ? state.dismissedNotificationIds
        : [...state.dismissedNotificationIds, id]
    })),
  updateCompanyName: (name) =>
    set((state) => ({
      brandProfile: {
        ...state.brandProfile,
        companyName: name
      }
    })),
  updateBrandProfile: (next) =>
    set((state) => ({
      brandProfile: {
        ...state.brandProfile,
        ...next
      }
    }))
}));
