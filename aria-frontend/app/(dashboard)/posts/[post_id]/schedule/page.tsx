import PostSchedulePageClient from "./page.client";

export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ post_id: "sample" }, { post_id: "preview-post-id" }];
}

export default function PostSchedulePage() {
  return <PostSchedulePageClient />;
}
