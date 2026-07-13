import bcrypt from "bcryptjs";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function upsertUser(input: {
  name: string;
  email: string;
  password: string;
  role: "agency_admin" | "brand_manager" | "content_creator" | "analyst";
}) {
  const hashedPassword = await bcrypt.hash(input.password, 12);

  const user = await prisma.user.upsert({
    where: { email: input.email },
    update: {
      name: input.name,
      password: hashedPassword,
      role: input.role
    },
    create: {
      name: input.name,
      email: input.email,
      password: hashedPassword,
      role: input.role
    }
  });
  const workspaceId = `workspace_${user.id}`;
  const brandId = `brand_${user.id}`;
  await prisma.aIWorkspace.upsert({
    where: { workspaceId },
    update: { name: `${input.name}'s workspace` },
    create: { workspaceId, name: `${input.name}'s workspace` }
  });
  await prisma.aIWorkspaceMembership.upsert({
    where: { workspaceId_userId: { workspaceId, userId: user.id } },
    update: { role: input.role },
    create: { workspaceId, userId: user.id, role: input.role }
  });
  await prisma.aIBrand.upsert({
    where: { brandId },
    update: { name: `${input.name} Brand` },
    create: { brandId, workspaceId, name: `${input.name} Brand` }
  });
}

async function main() {
  if (process.env.NODE_ENV === "production") {
    throw new Error("The local seed script cannot run in production.");
  }
  const starterPassword = process.env.ARIA_SEED_STARTER_PASSWORD;
  const adminPassword = process.env.ARIA_SEED_ADMIN_PASSWORD;
  if (!starterPassword || !adminPassword) {
    throw new Error("ARIA_SEED_STARTER_PASSWORD and ARIA_SEED_ADMIN_PASSWORD are required.");
  }
  await upsertUser({
    name: "Starter User",
    email: "starter@ariaconsole.com",
    password: starterPassword,
    role: "brand_manager"
  });

  await upsertUser({
    name: "Admin User",
    email: "admin@ariaconsole.com",
    password: adminPassword,
    role: "agency_admin"
  });

  console.log("Local seed users, workspaces, memberships, and brands created.");
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
