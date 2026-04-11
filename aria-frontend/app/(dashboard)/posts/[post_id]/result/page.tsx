import PostResultPageClient from "./page.client";

export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ post_id: "sample" }];
}

export default function PostResultPage() {
  return <PostResultPageClient />;
}
