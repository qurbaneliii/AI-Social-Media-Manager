import { getSupabasePublicConfig } from "@/lib/supabase/env";

type QueryParams = Record<string, string | number | boolean | null | undefined>;

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: QueryParams;
  accessToken?: string;
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

export const createSupabaseBrowserClient = () => {
  const { url, anonKey } = getSupabasePublicConfig();

  const request = async <T>(table: string, options: RequestOptions = {}): Promise<T> => {
    const method = options.method ?? "GET";
    const endpoint = `${url}/rest/v1/${table}${toQueryString(options.query)}`;
    const response = await fetch(endpoint, {
      method,
      headers: {
        apikey: anonKey,
        Authorization: `Bearer ${options.accessToken ?? anonKey}`,
        "Content-Type": "application/json",
        ...(options.prefer ? { Prefer: options.prefer } : {})
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Supabase request failed with ${response.status}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return (await response.json()) as T;
  };

  return {
    from: (table: string) => ({
      select: <T>(query?: QueryParams, accessToken?: string) =>
        request<T[]>(table, { method: "GET", query, accessToken }),
      insert: <T>(body: unknown, accessToken?: string) =>
        request<T[]>(table, { method: "POST", body, accessToken, prefer: "return=representation" }),
      update: <T>(body: unknown, query: QueryParams, accessToken?: string) =>
        request<T[]>(table, { method: "PATCH", body, query, accessToken, prefer: "return=representation" }),
      delete: <T>(query: QueryParams, accessToken?: string) =>
        request<T[]>(table, { method: "DELETE", query, accessToken, prefer: "return=representation" })
    })
  };
};
