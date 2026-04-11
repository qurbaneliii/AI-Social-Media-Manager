// filename: lib/query-client.ts
// purpose: Shared TanStack Query client instance.
// dependencies: @tanstack/react-query

import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});
