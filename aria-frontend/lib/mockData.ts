import type { UserRole } from "@/types";

export const PREVIEW_MODE_MESSAGE =
  "This feature requires a live server. Coming soon — running in preview mode.";

export const PREVIEW_COMPANY_ID = "00000000-0000-4000-8000-000000000001";

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
  name: "Aria Console",
  companyName: "Aria Console",
  industry: "SaaS",
  targetMarket: {
    regions: ["US", "UK", "CA"],
    segments: ["B2B"],
    personaSummary: "Growth-focused social teams that need faster content pipelines"
  },
  tone: ["confident", "clear", "modern"],
  platforms: ["linkedin", "twitter", "instagram"],
  postingFrequency: { linkedin: 2, twitter: 5, instagram: 3 },
  ctaTypes: ["learn_more", "book_demo"],
  brandColors: ["#0F766E", "#0077B5"],
  approvedVocabulary: ["innovative", "powerful", "seamless"],
  bannedVocabulary: ["cheap", "free", "spam"]
} as const;

export const mockStats = {
  totalPosts: 124,
  scheduledPosts: 8,
  publishedThisWeek: 23,
  engagementRate: "4.7%",
  reach: "12,400",
  impressions: "48,200"
} as const;

export const mockPosts = [
  {
    id: "1",
    platform: "linkedin",
    content:
      "Excited to share our latest product update! Our AI-powered pipeline just got smarter. Learn more about what we built. #AI #Product",
    status: "scheduled",
    scheduledFor: "2024-04-15 10:00",
    engagement: { likes: 0, comments: 0, shares: 0 }
  },
  {
    id: "2",
    platform: "twitter",
    content: "Big news dropping tomorrow. Stay tuned! #AriaConsole #SocialMedia",
    status: "published",
    scheduledFor: "2024-04-12 14:30",
    engagement: { likes: 47, comments: 12, shares: 8 }
  },
  {
    id: "3",
    platform: "instagram",
    content:
      "Behind the scenes of our content creation process. Swipe to see how we build. #BehindTheScenes #ContentCreation",
    status: "draft",
    scheduledFor: null,
    engagement: { likes: 0, comments: 0, shares: 0 }
  }
] as const;

export const mockAnalytics = {
  weeklyData: [
    { day: "Mon", posts: 3, engagement: 120 },
    { day: "Tue", posts: 5, engagement: 240 },
    { day: "Wed", posts: 2, engagement: 89 },
    { day: "Thu", posts: 6, engagement: 310 },
    { day: "Fri", posts: 4, engagement: 198 },
    { day: "Sat", posts: 1, engagement: 45 },
    { day: "Sun", posts: 2, engagement: 67 }
  ],
  platformBreakdown: [
    { platform: "LinkedIn", percentage: 40, color: "#0077B5" },
    { platform: "Twitter", percentage: 30, color: "#1DA1F2" },
    { platform: "Instagram", percentage: 20, color: "#E1306C" },
    { platform: "Facebook", percentage: 10, color: "#1877F2" }
  ]
} as const;

export const mockNotifications = [
  { id: "1", text: "3 posts scheduled for tomorrow", type: "info", time: "2 hours ago" },
  { id: "2", text: "LinkedIn post got 47 new likes", type: "success", time: "4 hours ago" },
  { id: "3", text: "Company profile setup incomplete", type: "warning", time: "1 day ago" }
] as const;

export const mockAIResponse = {
  linkedin: `🚀 Excited to announce a major milestone for our team! After months of development, we've launched our AI-powered social media pipeline that helps brands create, schedule, and optimize content at scale.

What makes it different? Our system understands your brand voice, respects your content guidelines, and generates platform-native content in seconds.

Ready to scale your social pipeline? Learn more ↓
#AI #SocialMedia #ContentMarketing #Innovation`,
  twitter: `Just shipped something big 🚀

AI-powered content pipeline for social media teams.
Create. Schedule. Optimize. At scale.

Learn more → ariaconsole.com
#AI #SocialMedia #ProductLaunch`
} as const;

export const mockGeneratedContent = {
  linkedin:
    "This is a preview of AI-generated LinkedIn content. Deploy with a live backend to enable real generation.",
  twitter:
    "Preview mode: AI content will appear here with live backend. #AriaConsole"
} as const;

export const PREVIEW_USER_STORAGE_KEY = "aria_preview_user";
