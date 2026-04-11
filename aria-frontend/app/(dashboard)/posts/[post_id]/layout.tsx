import type { ReactNode } from "react";

export const dynamicParams = false;

export async function generateStaticParams() {
  return [{ post_id: "sample" }];
}

type PostIdLayoutProps = {
  children: ReactNode;
};

export default function PostIdLayout({ children }: PostIdLayoutProps) {
  return children;
}
