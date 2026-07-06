import { readdirSync, readFileSync, statSync } from "node:fs";
import { extname, join, relative, sep } from "node:path";

const root = process.cwd();
const ignoredDirectories = new Set([
  ".git",
  ".next",
  "coverage",
  "dist",
  "node_modules",
  "out"
]);

const sourceExtensions = new Set([".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"]);
const sensitiveEnvNames = [
  "SUPABASE_SERVICE_ROLE_KEY",
  "OPENAI_API_KEY",
  "ANTHROPIC_API_KEY",
  "DATABASE_URL",
  "JWT_SECRET"
];
const forbiddenPublicServiceRoleName = "NEXT_PUBLIC_SUPABASE_" + "SERVICE_ROLE_KEY";

const failures = [];

const toPosix = (path) => path.split(sep).join("/");

const walk = (directory) => {
  return readdirSync(directory).flatMap((entry) => {
    const fullPath = join(directory, entry);
    const stats = statSync(fullPath);

    if (stats.isDirectory()) {
      return ignoredDirectories.has(entry) ? [] : walk(fullPath);
    }

    return stats.isFile() && sourceExtensions.has(extname(entry)) ? [fullPath] : [];
  });
};

const isClientFile = (path, contents) => {
  const normalized = toPosix(relative(root, path));
  const beginsWithUseClient = /^\s*["']use client["'];?/.test(contents);
  return (
    beginsWithUseClient ||
    normalized.startsWith("components/") ||
    normalized.startsWith("context/") ||
    normalized.startsWith("hooks/")
  );
};

const hasSensitiveEnvAccess = (contents, envName) => {
  const escaped = envName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`process\\.env(?:\\.${escaped}|\\[['"]${escaped}['"]\\])`).test(contents);
};

for (const file of walk(root)) {
  const normalized = toPosix(relative(root, file));
  const contents = readFileSync(file, "utf8");
  const clientFile = isClientFile(file, contents);

  if (contents.includes(forbiddenPublicServiceRoleName)) {
    failures.push(`${normalized}: never expose the Supabase service role key with NEXT_PUBLIC_`);
  }

  if (clientFile) {
    for (const envName of sensitiveEnvNames) {
      if (hasSensitiveEnvAccess(contents, envName)) {
        failures.push(`${normalized}: client-side code references server-only ${envName}`);
      }
    }

    if (
      contents.includes("@/lib/supabase/server") ||
      contents.includes("lib/supabase/server") ||
      contents.includes("createSupabaseAdminClient") ||
      contents.includes("getSupabaseServiceConfig")
    ) {
      failures.push(`${normalized}: client-side code imports or references the server-only Supabase helper`);
    }
  }
}

if (failures.length > 0) {
  console.error("Secret exposure check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("Secret exposure check passed.");
