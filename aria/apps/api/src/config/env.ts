import { config } from "dotenv";

config();

const required = [
  "DATABASE_URL",
  "REDIS_URL",
  "AWS_REGION",
  "AWS_S3_BUCKET",
  "AWS_KMS_KEY_ID",
  "AUTH0_DOMAIN",
  "AUTH0_AUDIENCE",
  "AUTH0_ISSUER_BASE_URL"
] as const;

for (const key of required) {
  if (!process.env[key]) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
}

export const env = {
  nodeEnv: process.env.NODE_ENV ?? "development",
  apiPort: Number(process.env.API_PORT ?? 4000),
  databaseUrl: process.env.DATABASE_URL!,
  redisUrl: process.env.REDIS_URL!,
  awsRegion: process.env.AWS_REGION!,
  s3Bucket: process.env.AWS_S3_BUCKET!,
  kmsKeyId: process.env.AWS_KMS_KEY_ID!,
  auth0Domain: process.env.AUTH0_DOMAIN!,
  auth0Audience: process.env.AUTH0_AUDIENCE!,
  auth0Issuer: process.env.AUTH0_ISSUER_BASE_URL!,
  webhookSecret: process.env.WEBHOOK_HMAC_SECRET ?? "",
  serviceToken: process.env.INTERNAL_SERVICE_TOKEN ?? ""
};
