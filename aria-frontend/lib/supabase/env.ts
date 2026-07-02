const requireEnv = (key: string): string => {
  const value = process.env[key];
  if (!value) {
    throw new Error(`${key} is not configured`);
  }
  return value;
};

export const getSupabasePublicConfig = () => ({
  url: requireEnv("NEXT_PUBLIC_SUPABASE_URL"),
  anonKey: requireEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
});

export const getSupabaseServiceConfig = () => ({
  url: requireEnv("NEXT_PUBLIC_SUPABASE_URL"),
  serviceRoleKey: requireEnv("SUPABASE_SERVICE_ROLE_KEY")
});
