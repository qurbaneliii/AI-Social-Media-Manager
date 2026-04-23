import type { ReactNode } from "react";

export const dynamicParams = false;

type PostIdLayoutProps = {
  children: ReactNode;
};

export default function PostIdLayout({ children }: PostIdLayoutProps) {
  return children;
}
