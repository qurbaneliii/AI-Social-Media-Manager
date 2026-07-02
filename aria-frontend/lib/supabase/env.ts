const requireValue = (key: string, value: string | undefined): string => {
  if (!value) {
    throw new Error(`${key} is not configured`);
  }
  return value;
};

export const getSupabasePublicConfig = () => ({
  url: requireValue("NEXT_PUBLIC_SUPABASE_URL", process.env.NEXT_PUBLIC_SUPABASE_URL),
  anonKey: requireValue("NEXT_PUBLIC_SUPABASE_ANON_KEY", process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY)
});

export const getSupabaseServiceConfig = () => ({
  url: requireValue("NEXT_PUBLIC_SUPABASE_URL", process.env.NEXT_PUBLIC_SUPABASE_URL),
  serviceRoleKey: requireValue("SUPABASE_SERVICE_ROLE_KEY", process.env.SUPABASE_SERVICE_ROLE_KEY)
});
