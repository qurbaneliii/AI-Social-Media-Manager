export class ApiBaseConfigurationError extends Error {
  readonly code = "API_BASE_URL_MISSING";
  readonly requiredEnv = "NEXT_PUBLIC_API_BASE_URL";

  constructor() {
    super("NEXT_PUBLIC_API_BASE_URL is not configured.");
    this.name = "ApiBaseConfigurationError";
  }
}

export function resolvePublicApiBase(): string {
  const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configuredBase) {
    return configuredBase.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return `${protocol}//${hostname}:8000`;
    }
  }

  throw new ApiBaseConfigurationError();
}
