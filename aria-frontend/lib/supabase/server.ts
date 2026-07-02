import "server-only";

import { getSupabaseServiceConfig } from "@/lib/supabase/env";

type QueryParams = Record<string, string | number | boolean | null | undefined>;

type AdminRequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: QueryParams;
  prefer?: string;
};

const toQueryString = (query: QueryParams = {}) => {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  });
  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
};

export const createSupabaseAdminClient = () => {
  const { url, serviceRoleKey } = getSupabaseServiceConfig();

  const request = async <T>(table: string, options: AdminRequestOptions = {}): Promise<T> => {
    const method = options.method ?? "GET";
    const endpoint = `${url}/rest/v1/${table}${toQueryString(options.query)}`;
    const response = await fetch(endpoint, {
      method,
      headers: {
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
        "Content-Type": "application/json",
        ...(options.prefer ? { Prefer: options.prefer } : {})
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Supabase admin request failed with ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  };

  return {
    from: (table: string) => ({
      select: <T>(query?: QueryParams) => request<T[]>(table, { method: "GET", query }),
      insert: <T>(body: unknown) => request<T[]>(table, { method: "POST", body, prefer: "return=representation" }),
      update: <T>(body: unknown, query: QueryParams) =>
        request<T[]>(table, { method: "PATCH", body, query, prefer: "return=representation" }),
      delete: <T>(query: QueryParams) =>
        request<T[]>(table, { method: "DELETE", query, prefer: "return=representation" })
    })
  };
};
