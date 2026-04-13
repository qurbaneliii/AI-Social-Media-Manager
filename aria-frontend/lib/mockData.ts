import type { UserRole } from "@/types";

export const PREVIEW_MODE_MESSAGE =
  "This feature requires a live server. Coming soon — running in preview mode.";

export const AUTH_PREVIEW_MESSAGE =
  "Authentication requires live server. Use preview mode to explore the UI.";

export const mockUser: {
  id: string;
  name: string;
  email: string;
  role: UserRole;
} = {
  id: "preview-user",
  name: "Preview User",
  email: "preview@ariaconsole.com",
  role: "brand_manager"
};

export const mockCompanyProfile = {
  platforms: ["linkedin", "twitter"],
  postingFrequency: { linkedin: 2, twitter: 5 },
  ctaTypes: ["learn_more"],
  brandColors: ["#0F766E"],
  approvedVocabulary: ["kapital"],
  bannedVocabulary: ["pul"]
} as const;

export const mockGeneratedContent = {
  linkedin:
    "This is a preview of AI-generated LinkedIn content. Deploy with a live backend to enable real generation.",
  twitter:
    "Preview mode: AI content will appear here with live backend. #AriaConsole"
} as const;

export const PREVIEW_USER_STORAGE_KEY = "aria_preview_user";
