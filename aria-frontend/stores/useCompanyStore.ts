// filename: stores/useCompanyStore.ts
// purpose: Global company, onboarding, workspace, and role state.
// dependencies: zustand, types

import { create } from "zustand";

import type { AgencyWorkspace, OnboardingStatus, Platform, PlatformCredentialStatus, UserRole } from "@/types";

const disconnectedState: PlatformCredentialStatus = { status: "disconnected" };

interface CompanyState {
  companyId: string | null;
  companyName: string | null;
  onboardingStep: number;
  onboardingScore: number | null;
  onboardingStatus: string | null;
  remediationList: string[];
  platformCredentials: Record<Platform, PlatformCredentialStatus>;
  activeRole: UserRole | null;
  workspaces: AgencyWorkspace[];
  activeWorkspaceId: string | null;
  setCompanyId: (id: string) => void;
  setOnboardingProgress: (status: OnboardingStatus) => void;
  updatePlatformCredential: (platform: Platform, status: PlatformCredentialStatus) => void;
  setActiveRole: (role: UserRole) => void;
  setActiveWorkspace: (id: string) => void;
}

export const useCompanyStore = create<CompanyState>((set) => ({
  companyId: null,
  companyName: null,
  onboardingStep: 1,
  onboardingScore: null,
  onboardingStatus: null,
  remediationList: [],
  platformCredentials: {
    instagram: disconnectedState,
    linkedin: disconnectedState,
    facebook: disconnectedState,
    x: disconnectedState,
    tiktok: disconnectedState,
    pinterest: disconnectedState
  },
  activeRole: null,
  workspaces: [],
  activeWorkspaceId: null,
  setCompanyId: (id) => set({ companyId: id }),
  setOnboardingProgress: (status) =>
    set({
      onboardingStep: status.step,
      onboardingScore: status.score,
      onboardingStatus: status.status,
      remediationList: status.remediation ?? []
    }),
  updatePlatformCredential: (platform, status) =>
    set((state) => ({
      platformCredentials: {
        ...state.platformCredentials,
        [platform]: status
      }
    })),
  setActiveRole: (role) => set({ activeRole: role }),
  setActiveWorkspace: (id) => set({ activeWorkspaceId: id })
}));
