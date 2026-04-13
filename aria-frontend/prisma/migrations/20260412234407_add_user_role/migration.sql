-- CreateEnum
CREATE TYPE "public"."UserRole" AS ENUM ('agency_admin', 'brand_manager', 'content_creator', 'analyst');

-- AlterTable
ALTER TABLE "public"."User"
ADD COLUMN     "role" "public"."UserRole";

-- Backfill existing users before enforcing NOT NULL.
UPDATE "public"."User"
SET "role" = 'brand_manager'
WHERE "role" IS NULL;

ALTER TABLE "public"."User"
ALTER COLUMN "role" SET NOT NULL,
DROP COLUMN "updatedAt";
