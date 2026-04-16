import type { ReactNode } from "react";

export const dynamicParams = true;

type PostIdLayoutProps = {
  children: ReactNode;
};

export default function PostIdLayout({ children }: PostIdLayoutProps) {
  return children;
}
