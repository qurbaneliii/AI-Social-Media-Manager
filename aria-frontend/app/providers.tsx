// filename: app/providers.tsx
// purpose: Client-side providers for query cache and global toasts.

"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

import { AuthProvider } from "@/context/AuthContext";
import { queryClient } from "@/lib/query-client";
import { ThemeProvider } from "@/components/providers/theme-provider";

export const Providers = ({ children }: { children: React.ReactNode }) => {
  return (
    <ThemeProvider attribute="data-theme" defaultTheme="system" enableSystem>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          {children}
          <Toaster richColors position="bottom-right" />
        </QueryClientProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};
