"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import type { UserRole } from "@/types";

const roleOptions: UserRole[] = ["agency_admin", "brand_manager", "content_creator", "analyst"];

export default function RegisterPage() {
  const router = useRouter();
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<UserRole | "">("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{
    name?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    role?: string;
    general?: string;
  }>({});

  const emailValid = useMemo(() => /\S+@\S+\.\S+/.test(email), [email]);
  const passwordValid = password.length >= 8;
  const passwordsMatch = password === confirmPassword;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const nextErrors: {
      name?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
      role?: string;
      general?: string;
    } = {};

    if (!name.trim()) {
      nextErrors.name = "Full name is required.";
    }

    if (!emailValid) {
      nextErrors.email = "Please enter a valid email address.";
    }
    if (!passwordValid) {
      nextErrors.password = "Password must be at least 8 characters.";
    }
    if (!passwordsMatch) {
      nextErrors.confirmPassword = "Confirm password must match password.";
    }
    if (!role) {
      nextErrors.role = "Please select a role.";
    }

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      await register({ name: name.trim(), email: email.trim(), password, role: role as UserRole });
      router.push("/login?registered=1");
    } catch (submitError) {
      const message = submitError instanceof Error ? submitError.message : "Failed to create account.";
      setErrors((prev) => ({
        ...prev,
        general: message.includes("exists") ? "Email already exists." : message
      }));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center justify-center px-4 py-8">
      <section className="grid w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl md:grid-cols-2">
        <div className="bg-gradient-to-br from-teal-700 via-sky-700 to-cyan-700 p-8 text-white">
          <p className="text-xs uppercase tracking-[0.2em] text-cyan-100">ARIA Console</p>
          <h1 className="mt-3 text-3xl font-semibold">Scale your social pipeline</h1>
          <p className="mt-4 text-sm text-cyan-100">Generate platform-native content, review quality signals, and schedule with confidence.</p>
        </div>

        <form onSubmit={submit} className="space-y-4 p-8">
          <h2 className="text-xl font-semibold text-slate-900">Create account</h2>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Full Name</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="Jane Doe"
            />
            {errors.name ? <p className="text-xs text-red-600">{errors.name}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              placeholder="you@company.com"
            />
            {errors.email ? <p className="text-xs text-red-600">{errors.email}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
            {errors.password ? <p className="text-xs text-red-600">{errors.password}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Confirm Password</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
            {errors.confirmPassword ? <p className="text-xs text-red-600">{errors.confirmPassword}</p> : null}
          </label>

          <label className="block space-y-1 text-sm text-slate-700">
            <span>Role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole | "")}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">Select role</option>
              {roleOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            {errors.role ? <p className="text-xs text-red-600">{errors.role}</p> : null}
          </label>

          {errors.general ? <p className="text-xs text-red-600">{errors.general}</p> : null}

          <button className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>

          <p className="text-sm text-slate-600">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-slate-900 underline">
              Sign in
            </Link>
          </p>
        </form>
      </section>
    </main>
  );
}
