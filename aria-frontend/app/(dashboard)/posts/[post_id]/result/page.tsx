import PostResultPageClient from "./page.client";

export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ post_id: "sample" }, { post_id: "preview-post-id" }];
}

export default function PostResultPage() {
  return <PostResultPageClient />;
}
