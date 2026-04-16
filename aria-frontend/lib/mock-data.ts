export type DashboardPlatform = "linkedin" | "twitter" | "instagram" | "facebook";
export type PostStatus = "scheduled" | "published" | "draft" | "failed";
export type NotificationType = "info" | "success" | "warning" | "error";

export interface StatMetric {
  id: string;
  title: string;
  value: number;
  valuePrefix?: string;
  valueSuffix?: string;
  change: number;
  changeLabel: string;
  icon: "FileText" | "Clock3" | "Send" | "TrendingUp" | "Eye" | "BarChart3";
  trend: number[];
}

export interface WeeklyMetric {
  day: string;
  posts: number;
  engagement: number;
}

export interface PlatformBreakdown {
  platform: DashboardPlatform;
  value: number;
  count: number;
  color: string;
}

export interface PostMetric {
  likes: number;
  comments: number;
  shares: number;
}

export interface DashboardPost {
  id: string;
  platform: DashboardPlatform;
  status: PostStatus;
  content: string;
  scheduledAt?: string;
  metrics: PostMetric;
}

export interface DashboardNotification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export interface BrandProfile {
  companyName: string;
  platforms: DashboardPlatform[];
  postingFrequency: number[];
  colors: string[];
  approvedVocabulary: string[];
  bannedVocabulary: string[];
  completion: number;
}

export const platformLabels: Record<DashboardPlatform, string> = {
  linkedin: "LinkedIn",
  twitter: "Twitter/X",
  instagram: "Instagram",
  facebook: "Facebook"
};

export const platformCharacterLimits: Record<DashboardPlatform, number> = {
  linkedin: 3000,
  twitter: 280,
  instagram: 2200,
  facebook: 63206
};

export const statMetrics: StatMetric[] = [
  {
    id: "total-posts",
    title: "Total Posts",
    value: 124,
    change: 12.5,
    changeLabel: "vs last week",
    icon: "FileText",
    trend: [12, 13, 15, 14, 17, 18, 20]
  },
  {
    id: "scheduled",
    title: "Scheduled",
    value: 8,
    change: 4.2,
    changeLabel: "in queue",
    icon: "Clock3",
    trend: [4, 5, 5, 6, 7, 8, 8]
  },
  {
    id: "published-week",
    title: "Published This Week",
    value: 23,
    change: 18.2,
    changeLabel: "vs prior week",
    icon: "Send",
    trend: [2, 3, 4, 4, 3, 4, 3]
  },
  {
    id: "engagement-rate",
    title: "Engagement Rate",
    value: 4.7,
    valueSuffix: "%",
    change: 1.6,
    changeLabel: "vs last week",
    icon: "TrendingUp",
    trend: [3.8, 4.1, 4.0, 4.4, 4.5, 4.6, 4.7]
  },
  {
    id: "reach",
    title: "Reach",
    value: 12400,
    change: 8.9,
    changeLabel: "weekly change",
    icon: "Eye",
    trend: [8200, 9100, 9700, 10300, 10800, 11700, 12400]
  },
  {
    id: "impressions",
    title: "Impressions",
    value: 48200,
    change: -2.1,
    changeLabel: "vs last week",
    icon: "BarChart3",
    trend: [42000, 43800, 45100, 46700, 49300, 48800, 48200]
  }
];

export const weeklyPerformance: WeeklyMetric[] = [
  { day: "Mon", posts: 3, engagement: 120 },
  { day: "Tue", posts: 5, engagement: 240 },
  { day: "Wed", posts: 2, engagement: 89 },
  { day: "Thu", posts: 6, engagement: 310 },
  { day: "Fri", posts: 4, engagement: 198 },
  { day: "Sat", posts: 1, engagement: 45 },
  { day: "Sun", posts: 2, engagement: 67 }
];

export const platformBreakdown: PlatformBreakdown[] = [
  { platform: "linkedin", value: 43, count: 53, color: "#0077B5" },
  { platform: "twitter", value: 21, count: 26, color: "#000000" },
  { platform: "instagram", value: 24, count: 30, color: "#E1306C" },
  { platform: "facebook", value: 12, count: 15, color: "#1877F2" }
];

export const recentPosts: DashboardPost[] = [
  {
    id: "p-1",
    platform: "linkedin",
    status: "scheduled",
    content: "How B2B teams are reducing ad waste with prompt-based creative testing this quarter.",
    scheduledAt: "2026-04-17T10:00:00.000Z",
    metrics: { likes: 45, comments: 8, shares: 6 }
  },
  {
    id: "p-2",
    platform: "twitter",
    status: "published",
    content: "Growth is not a lucky spike. It is a repeatable process with measurable creative loops.",
    metrics: { likes: 112, comments: 27, shares: 19 }
  },
  {
    id: "p-3",
    platform: "instagram",
    status: "draft",
    content: "From strategy board to launch in one flow. Behind the scenes of our weekly content sprint.",
    metrics: { likes: 0, comments: 0, shares: 0 }
  },
  {
    id: "p-4",
    platform: "facebook",
    status: "failed",
    content: "A practical playbook for teams who need fast approvals without quality dropping.",
    metrics: { likes: 9, comments: 1, shares: 2 }
  }
];

export const notifications: DashboardNotification[] = [
  {
    id: "n-1",
    type: "warning",
    title: "Post failed on Facebook",
    message: "Publishing failed because token permissions expired.",
    timestamp: "2026-04-16T09:20:00.000Z",
    read: false
  },
  {
    id: "n-2",
    type: "success",
    title: "LinkedIn queue synced",
    message: "All scheduled posts for this week are now synced.",
    timestamp: "2026-04-16T07:02:00.000Z",
    read: false
  },
  {
    id: "n-3",
    type: "info",
    title: "Weekly report generated",
    message: "Analytics summary is ready in the insights panel.",
    timestamp: "2026-04-15T19:40:00.000Z",
    read: true
  },
  {
    id: "n-4",
    type: "error",
    title: "API latency spike",
    message: "Generation requests exceeded 2.5s in the last hour.",
    timestamp: "2026-04-15T16:10:00.000Z",
    read: true
  }
];

export const defaultBrandProfile: BrandProfile = {
  companyName: "ARIA Labs",
  platforms: ["linkedin", "twitter", "instagram"],
  postingFrequency: [2, 3, 4, 4, 3, 2, 1],
  colors: ["#0F766E", "#0077B5"],
  approvedVocabulary: ["innovative", "powerful", "seamless"],
  bannedVocabulary: ["cheap", "free", "spam"],
  completion: 75
};

export const aiToneOptions = ["Professional", "Confident", "Friendly", "Casual", "Bold"] as const;
export const aiCtaOptions = ["Learn More", "Book Demo", "Download", "Sign Up"] as const;
export const aiPlatformOptions: DashboardPlatform[] = ["linkedin", "twitter", "instagram"];
