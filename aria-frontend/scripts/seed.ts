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

  await prisma.user.upsert({
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
}

async function main() {
  await upsertUser({
    name: "Starter User",
    email: "starter@ariaconsole.com",
    password: "Starter123!",
    role: "brand_manager"
  });

  await upsertUser({
    name: "Admin User",
    email: "admin@ariaconsole.com",
    password: "Admin123!",
    role: "agency_admin"
  });

  console.log("Seed users created");
  console.log("Email: starter@ariaconsole.com | Password: Starter123!");
  console.log("Email: admin@ariaconsole.com | Password: Admin123!");
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
