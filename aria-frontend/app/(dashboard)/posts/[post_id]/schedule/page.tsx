import PostSchedulePageClient from "./page.client";

export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ post_id: "sample" }];
}

export default function PostSchedulePage() {
  return <PostSchedulePageClient />;
}
