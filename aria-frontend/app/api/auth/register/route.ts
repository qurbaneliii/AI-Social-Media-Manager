import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { z } from "zod";

import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

const roleSchema = z.enum(["agency_admin", "brand_manager", "content_creator", "analyst"]);

const registerSchema = z.object({
  name: z.string().trim().min(1).max(120),
  email: z.string().trim().email(),
  password: z.string().min(8),
  role: roleSchema
});

export async function POST(request: Request) {
  try {
    const payload = registerSchema.parse(await request.json());
    const existing = await prisma.user.findUnique({ where: { email: payload.email } });

    if (existing) {
      return NextResponse.json({ error: "Email already exists" }, { status: 409 });
    }

    const hashedPassword = await bcrypt.hash(payload.password, 12);

    const user = await prisma.$transaction(async (transaction) => {
      const createdUser = await transaction.user.create({
        data: {
          name: payload.name,
          email: payload.email,
          password: hashedPassword,
          role: payload.role
        }
      });
      const workspaceId = `workspace_${createdUser.id}`;
      const brandId = `brand_${createdUser.id}`;
      await transaction.aIWorkspace.create({
        data: {
          workspaceId,
          name: `${payload.name}'s workspace`,
          memberships: {
            create: { userId: createdUser.id, role: payload.role }
          },
          brands: {
            create: { brandId, name: payload.name }
          }
        }
      });
      return createdUser;
    });

    return NextResponse.json(
      {
        message: "User created",
        user: { id: user.id, email: user.email, role: user.role }
      },
      { status: 201 }
    );
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: "Invalid input",
          details: error.flatten()
        },
        { status: 400 }
      );
    }

    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
