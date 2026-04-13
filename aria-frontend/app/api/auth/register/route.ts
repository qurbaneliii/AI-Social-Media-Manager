import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { z } from "zod";

import { prisma } from "@/lib/prisma";

const isStatic = process.env.NEXT_PUBLIC_IS_STATIC === "true";

export const dynamic = "force-static";

const roleSchema = z.enum(["agency_admin", "brand_manager", "content_creator", "analyst"]);

const registerSchema = z.object({
  name: z.string().trim().min(1).max(120),
  email: z.string().trim().email(),
  password: z.string().min(8),
  role: roleSchema
});

export async function POST(request: Request) {
  if (isStatic) {
    return NextResponse.json({ error: "Authentication requires a live server." }, { status: 503 });
  }

  try {
    const payload = registerSchema.parse(await request.json());
    const existing = await prisma.user.findUnique({ where: { email: payload.email } });

    if (existing) {
      return NextResponse.json({ error: "Email already exists" }, { status: 409 });
    }

    const hashedPassword = await bcrypt.hash(payload.password, 12);

    const user = await prisma.user.create({
      data: {
        name: payload.name,
        email: payload.email,
        password: hashedPassword,
        role: payload.role
      },
      select: {
        id: true,
        email: true,
        role: true
      }
    });

    return NextResponse.json(
      {
        message: "User created",
        user
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
